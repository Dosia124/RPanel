import os
import io
import json
import shutil
import mimetypes
import webbrowser
import base64
import tempfile
import time
import signal
from threading import Timer, Thread
from flask import Flask, request, session, redirect, url_for, jsonify, Response
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from PIL import Image

# Опциональный импорт для видео-превью
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# ================== CONFIG ==================
INBOX_FOLDER = "inbox"
VAULTS_DIR = "vaults"
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.mkv', '.webm', '.mov')
SALT_FILE = "salt.bin"
MASTER_KEY_FILE = "master.key.enc"
VAULT_REGISTRY_FILE = "vaults.enc"
CURRENT_KEY = None
LAST_PING = time.time()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ================== VAULT CORE ==================
def get_salt():
    if not os.path.exists(SALT_FILE):
        with open(SALT_FILE, 'wb') as f: f.write(os.urandom(16))
    with open(SALT_FILE, 'rb') as f: return f.read()

def derive_key(password):
    salt = get_salt()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def change_password(old_pass, new_pass):
    if not os.path.exists(MASTER_KEY_FILE):
        return False, "Vault does not exist yet. Start the server first to create it."
    try:
        with open(MASTER_KEY_FILE, 'rb') as f: enc_master = f.read()
        master_key = Fernet(derive_key(old_pass)).decrypt(enc_master)
        new_enc_master = Fernet(derive_key(new_pass)).encrypt(master_key)
        with open(MASTER_KEY_FILE, 'wb') as f: f.write(new_enc_master)
        return True, "Password changed successfully!"
    except InvalidToken:
        return False, "Old password is incorrect!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_master_key(password):
    global CURRENT_KEY
    if not os.path.exists(MASTER_KEY_FILE):
        master_key = Fernet.generate_key()
        enc_master = Fernet(derive_key(password)).encrypt(master_key)
        with open(MASTER_KEY_FILE, 'wb') as f: f.write(enc_master)
        CURRENT_KEY = master_key
        return master_key
    else:
        try:
            with open(MASTER_KEY_FILE, 'rb') as f: enc_master = f.read()
            master_key = Fernet(derive_key(password)).decrypt(enc_master)
            CURRENT_KEY = master_key
            return master_key
        except InvalidToken:
            return None

def get_vault_path(vault_id):
    return os.path.join(VAULTS_DIR, vault_id)

def get_vaults():
    if not os.path.exists(VAULT_REGISTRY_FILE):
        return []
    try:
        with open(VAULT_REGISTRY_FILE, 'rb') as f: enc_data = f.read()
        dec_data = Fernet(CURRENT_KEY).decrypt(enc_data)
        return json.loads(dec_data)
    except:
        return []

def save_vaults(vaults):
    if not CURRENT_KEY: return
    enc_data = Fernet(CURRENT_KEY).encrypt(json.dumps(vaults).encode())
    with open(VAULT_REGISTRY_FILE, 'wb') as f: f.write(enc_data)

def load_tags(vault_id):
    path = os.path.join(get_vault_path(vault_id), "tags.enc")
    if not os.path.exists(path): return {}
    try:
        with open(path, 'rb') as f: enc_data = f.read()
        dec_data = Fernet(CURRENT_KEY).decrypt(enc_data)
        return json.loads(dec_data)
    except:
        return {}

def save_tags(vault_id, tags):
    if not CURRENT_KEY: return
    path = os.path.join(get_vault_path(vault_id), "tags.enc")
    enc_data = Fernet(CURRENT_KEY).encrypt(json.dumps(tags).encode())
    with open(path, 'wb') as f: f.write(enc_data)

# ================== SERVER LOGIC ==================
def get_files_list(vault_id):
    path = get_vault_path(vault_id)
    if not os.path.exists(path): return []
    files = []
    for f in os.listdir(path):
        if f.endswith('.enc') and f != 'tags.enc':
            original_name = f[:-4]
            ext = os.path.splitext(original_name)[1].lower()
            if ext in ALLOWED_EXTENSIONS: files.append(original_name)
    return sorted(files)

@app.route('/')
def index():
    if not session.get('authed'): return LOGIN_HTML
    return MAIN_HTML

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    master_key = get_master_key(password)
    if master_key:
        session['authed'] = True
        global LAST_PING
        LAST_PING = time.time()
        
        vaults = get_vaults()
        if len(vaults) == 0:
            vault_id = os.urandom(8).hex()
            vaults.append({"id": vault_id, "name": "Default"})
            save_vaults(vaults)
            os.makedirs(get_vault_path(vault_id), exist_ok=True)
            session['current_vault'] = vault_id
        else:
            session['current_vault'] = vaults[0]['id']
            
        return redirect(url_for('index'))
    return "Invalid password! <a href='/'>Back</a>"

@app.route('/api/vaults')
def api_get_vaults():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    return jsonify({"vaults": get_vaults(), "current": session.get('current_vault')})

@app.route('/api/vaults/create', methods=['POST'])
def api_create_vault():
    if not session.get('authed') or not CURRENT_KEY: return jsonify({"error": "Not authed"}), 403
    name = request.json.get('name')
    if not name: return jsonify({"error": "Name required"}), 400
    
    vault_id = os.urandom(8).hex()
    vaults = get_vaults()
    vaults.append({"id": vault_id, "name": name})
    save_vaults(vaults)
    os.makedirs(get_vault_path(vault_id), exist_ok=True)
    session['current_vault'] = vault_id
    return jsonify({"success": True, "id": vault_id})

@app.route('/api/vaults/switch', methods=['POST'])
def api_switch_vault():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    vault_id = request.json.get('id')
    vaults = get_vaults()
    if any(v['id'] == vault_id for v in vaults):
        session['current_vault'] = vault_id
        return jsonify({"success": True})
    return jsonify({"error": "Vault not found"}), 404

@app.route('/api/vaults/delete', methods=['POST'])
def api_delete_vault():
    if not session.get('authed') or not CURRENT_KEY: return jsonify({"error": "Not authed"}), 403
    vault_id = request.json.get('id')
    vaults = get_vaults()
    new_vaults = [v for v in vaults if v['id'] != vault_id]
    if len(new_vaults) == len(vaults): return jsonify({"error": "Not found"}), 404
    
    path = get_vault_path(vault_id)
    if os.path.exists(path):
        shutil.rmtree(path)
        
    save_vaults(new_vaults)
    
    if session.get('current_vault') == vault_id:
        if len(new_vaults) > 0:
            session['current_vault'] = new_vaults[0]['id']
        else:
            default_id = os.urandom(8).hex()
            new_vaults.append({"id": default_id, "name": "Default"})
            save_vaults(new_vaults)
            os.makedirs(get_vault_path(default_id), exist_ok=True)
            session['current_vault'] = default_id
            
    return jsonify({"success": True})

@app.route('/api/files')
def api_files():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    current_vault = session.get('current_vault')
    if not current_vault: return jsonify({"error": "No vault selected"}), 400
    
    inbox_count = 0
    if os.path.exists(INBOX_FOLDER):
        inbox_count = len([f for f in os.listdir(INBOX_FOLDER) if f.lower().endswith(ALLOWED_EXTENSIONS)])
    
    resp = jsonify({"files": get_files_list(current_vault), "inbox_count": inbox_count, "tags": load_tags(current_vault)})
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/api/import', methods=['POST'])
def api_import():
    if not session.get('authed') or not CURRENT_KEY: return jsonify({"error": "Not authed"}), 403
    current_vault = session.get('current_vault')
    fernet = Fernet(CURRENT_KEY)
    imported = 0
    if os.path.exists(INBOX_FOLDER):
        for f in os.listdir(INBOX_FOLDER):
            if f.lower().endswith(ALLOWED_EXTENSIONS):
                filepath = os.path.join(INBOX_FOLDER, f)
                if os.path.isfile(filepath):
                    with open(filepath, 'rb') as file: data = file.read()
                    enc_data = fernet.encrypt(data)
                    with open(os.path.join(get_vault_path(current_vault), f + '.enc'), 'wb') as enc_file: enc_file.write(enc_data)
                    os.remove(filepath)
                    imported += 1
    return jsonify({"success": True, "imported": imported})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if not session.get('authed') or not CURRENT_KEY: return jsonify({"error": "Not authed"}), 403
    current_vault = session.get('current_vault')
    if 'files[]' not in request.files: return jsonify({"error": "No files"}), 400
    
    fernet = Fernet(CURRENT_KEY)
    uploaded = 0
    for file in request.files.getlist('files[]'):
        if file.filename == '': continue
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            data = file.read()
            enc_data = fernet.encrypt(data)
            with open(os.path.join(get_vault_path(current_vault), filename + '.enc'), 'wb') as f:
                f.write(enc_data)
            uploaded += 1
    return jsonify({"success": True, "uploaded": uploaded})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    if not session.get('authed') or not CURRENT_KEY: return jsonify({"error": "Not authed"}), 403
    current_vault = session.get('current_vault')
    filename = request.json.get('filename')
    if not filename: return jsonify({"error": "No file"}), 400
    enc_filepath = os.path.join(get_vault_path(current_vault), filename + ".enc")
    if os.path.exists(enc_filepath):
        os.remove(enc_filepath)
        return jsonify({"success": True})
    return jsonify({"error": "File not found"}), 404

@app.route('/api/tags/update', methods=['POST'])
def api_tags_update():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    current_vault = session.get('current_vault')
    data = request.json
    filename = data.get('filename')
    tags = data.get('tags', [])
    if not filename: return jsonify({"error": "No file"}), 400
    
    all_tags = load_tags(current_vault)
    all_tags[filename] = tags
    save_tags(current_vault, all_tags)
    return jsonify({"success": True})

@app.route('/api/change_password', methods=['POST'])
def api_change_password():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    data = request.json
    old_pass = data.get('old_pass')
    new_pass = data.get('new_pass')
    if not old_pass or not new_pass: return jsonify({"error": "Missing data"}), 400
    if len(new_pass) < 4: return jsonify({"error": "Password must be at least 4 characters"}), 400
    
    success, message = change_password(old_pass, new_pass)
    if success:
        return jsonify({"success": True, "message": message})
    return jsonify({"error": message}), 400

@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    if not session.get('authed'): return jsonify({"error": "Not authed"}), 403
    Timer(1.0, os.kill, args=[os.getpid(), signal.SIGINT]).start()
    return jsonify({"success": True})

@app.route('/api/ping', methods=['POST'])
def api_ping():
    global LAST_PING
    LAST_PING = time.time()
    return jsonify({"success": True})

@app.route('/thumbnail/<filename>')
def get_thumbnail(filename):
    if not session.get('authed') or not CURRENT_KEY: return "Forbidden", 403
    current_vault = session.get('current_vault')
    enc_filepath = os.path.join(get_vault_path(current_vault), filename + ".enc")
    if not os.path.exists(enc_filepath): return "File not found", 404

    fernet = Fernet(CURRENT_KEY)
    with open(enc_filepath, 'rb') as f: enc_data = f.read()
    dec_data = fernet.decrypt(enc_data)
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ('.mp4', '.mkv', '.webm', '.mov'):
        if not HAS_CV2: return "CV2 not installed", 404
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_video:
                temp_video.write(dec_data)
                temp_path = temp_video.name
            
            cap = cv2.VideoCapture(temp_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                if img.mode in ("RGBA", "P", "LA"): img = img.convert("RGB")
                img.thumbnail((400, 400))
                img_io = io.BytesIO()
                img.save(img_io, 'JPEG', quality=95)
                img_io.seek(0)
                return Response(img_io.getvalue(), mimetype='image/jpeg')
        except Exception as e:
            pass
        finally:
            if temp_path and os.path.exists(temp_path): os.remove(temp_path)
        return "Error generating video thumbnail", 500

    try:
        img = Image.open(io.BytesIO(dec_data))
        img.seek(0)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
            
        img.thumbnail((400, 400))
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return Response(img_io.getvalue(), mimetype='image/jpeg')
    except Exception as e:
        return "Error generating thumbnail", 500

@app.route('/media/<filename>')
def get_media(filename):
    if not session.get('authed') or not CURRENT_KEY: return "Forbidden", 403
    current_vault = session.get('current_vault')
    enc_filepath = os.path.join(get_vault_path(current_vault), filename + ".enc")
    if not os.path.exists(enc_filepath): return "File not found", 404

    fernet = Fernet(CURRENT_KEY)
    with open(enc_filepath, 'rb') as f: enc_data = f.read()
    dec_data = fernet.decrypt(enc_data)
    
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type: mime_type = 'application/octet-stream'

    range_header = request.headers.get('Range', None)
    total_size = len(dec_data)
    if range_header:
        start, end = range_header.replace('bytes=', '').split('-')
        start = int(start)
        end = int(end) if end else total_size - 1
        chunk = dec_data[start:end+1]
        headers = {'Content-Range': f'bytes {start}-{end}/{total_size}', 'Accept-Ranges': 'bytes', 'Content-Length': str(len(chunk)), 'Content-Type': mime_type}
        return Response(chunk, 206, headers)
    else:
        return Response(dec_data, 200, {'Content-Type': mime_type, 'Content-Length': str(total_size), 'Accept-Ranges': 'bytes'})

# ================== HTML TEMPLATES ==================
LOGIN_HTML = '''
<!DOCTYPE html>
<html><head><title>Vault Access</title>
<style>
:root { --bg: #0f0f10; --surface: #1c1c1e; --text: #ffffff; --accent: #0a84ff; }
body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.card { background: var(--surface); padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 24px 60px rgba(0,0,0,0.5); width: 360px; }
.icon { margin-bottom: 20px; color: var(--accent); }
h2 { margin: 0 0 20px 0; font-weight: 600; }
input { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); padding: 15px; width: 100%; border-radius: 12px; margin-bottom: 20px; color: var(--text); font-size: 16px; box-sizing: border-box; }
input:focus { outline: none; border-color: var(--accent); }
button { background: var(--accent); border: none; padding: 15px; width: 100%; border-radius: 12px; color: #fff; cursor: pointer; font-weight: 600; font-size: 16px; transition: transform 0.1s, filter 0.2s; }
button:hover { filter: brightness(1.1); }
button:active { transform: scale(0.98); }
</style></head>
<body>
<form class="card" method="POST" action="/login">
    <div class="icon"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div>
    <h2>Vault Access</h2>
    <input type="password" name="password" placeholder="Enter Password" autofocus>
    <button type="submit">Unlock</button>
</form>
</body></html>
'''

MAIN_HTML = '''
<!DOCTYPE html>
<html><head><title>Media Vault</title>
<style>
:root { --bg: #0f0f10; --surface: #1c1c1e; --surface-hover: #2c2c2e; --text: #ffffff; --text-dim: #8e8e93; --accent: #0a84ff; --danger: #ff453a; --grid-size: 150px; }
body.light-theme { --bg: #f2f2f7; --surface: #ffffff; --surface-hover: #e5e5ea; --text: #000000; --text-dim: #8e8e93; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; overflow: hidden; transition: background 0.3s; }
::-webkit-scrollbar { width: 8px; height: 8px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: var(--surface-hover); border-radius: 4px; }
#top-bar { position: fixed; top:0; left:0; width:100%; padding:15px 20px; background: rgba(0,0,0,0.3); backdrop-filter: blur(20px); display:flex; justify-content:space-between; align-items:center; z-index:100; border-bottom: 1px solid rgba(255,255,255,0.1); }
body.light-theme #top-bar { background: rgba(255,255,255,0.6); border-bottom: 1px solid rgba(0,0,0,0.1); }
.top-left { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.logo { font-weight: 700; font-size: 18px; display: flex; align-items: center; gap: 8px; }

.dropdown { position: relative; display: inline-block; }
.dropbtn { background: var(--surface); border: none; color: var(--text); padding: 8px 15px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 8px; transition: background 0.2s; max-width: 200px; }
.dropbtn span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dropbtn:hover { background: var(--surface-hover); }
.dropdown-content { display: none; position: absolute; top: 45px; left: 0; background: var(--surface); min-width: 180px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); z-index: 101; border-radius: 12px; padding: 6px; border: 1px solid rgba(255,255,255,0.1); max-height: 300px; overflow-y: auto; }
body.light-theme .dropdown-content { border: 1px solid rgba(0,0,0,0.1); }
.dropdown-content.show { display: block; }
.dropdown-item { padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px; color: var(--text); transition: background 0.2s; user-select: none; display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.dropdown-item:hover { background: var(--surface-hover); }
.dropdown-item input[type="checkbox"] { margin: 0; width: 16px; height: 16px; accent-color: var(--accent); cursor: pointer; }
.dropdown-item.danger { color: var(--danger); }
.dropdown-item.accent { color: var(--accent); }

.search-wrapper { position: relative; display: flex; align-items: center; background: var(--surface); border-radius: 8px; border: 1px solid transparent; transition: border-color 0.2s, width 0.3s; width: 150px; }
.search-wrapper:focus-within { border-color: var(--accent); width: 300px; }
.search-wrapper svg { color: var(--text-dim); margin-left: 10px; flex-shrink: 0; }
.search-input { background: transparent; border: none; color: var(--text); padding: 8px 12px; font-size: 13px; width: 100%; outline: none; }
.search-input::placeholder { color: var(--text-dim); }
.suggestions-box { display: none; position: absolute; top: 100%; left: 0; right: 0; background: var(--surface); border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); z-index: 102; padding: 5px; margin-top: 5px; max-height: 250px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1); }
body.light-theme .suggestions-box { border: 1px solid rgba(0,0,0,0.1); }
.suggestions-box.show { display: block; }
.suggestion-item { padding: 8px 12px; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; font-size: 13px; }
.suggestion-item:hover, .suggestion-item.active { background: var(--surface-hover); }
.suggestion-count { color: var(--text-dim); font-size: 11px; background: var(--bg); padding: 2px 6px; border-radius: 4px; }

.top-right { display: flex; align-items: center; gap: 15px; }
.icon-btn { background: var(--surface); border: none; color: var(--text); width: 40px; height: 40px; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; position: relative; }
.icon-btn:hover { background: var(--surface-hover); }
.icon-btn.danger:hover { background: var(--danger); }
.badge { position: absolute; top: -5px; right: -5px; background: var(--accent); color: #fff; font-size: 10px; font-weight: bold; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid var(--bg); }
#gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--grid-size), 1fr)); gap: 12px; padding: 80px 20px 20px; height: 100vh; overflow-y: auto; align-content: start; }
.media-item { width: 100%; height: var(--grid-size); object-fit: cover; cursor: pointer; background: var(--surface); border-radius: 12px; transition: transform 0.2s, box-shadow 0.2s; }
.media-item:hover { transform: scale(1.02); box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
#viewer { position: fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.95); display:none; justify-content:center; align-items:center; z-index: 99; }
#media-img, #media-video { max-width: 90%; max-height: 85%; transition: transform 0.1s ease-out; border-radius: 4px; transform-origin: center center; }
#media-video { width: 90%; height: 85%; object-fit: contain; background: #000; }
.viewer-controls { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); background: var(--surface); padding: 10px; border-radius: 16px; display: flex; gap: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); z-index: 100; }
.vc-btn { background: transparent; border: none; color: #fff; width: 44px; height: 44px; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
.vc-btn:hover { background: var(--surface-hover); } .vc-btn.danger:hover { background: var(--danger); }
.hint { position: fixed; bottom: 10px; right: 20px; color: var(--text-dim); font-size: 12px; z-index: 100; transition: opacity 0.3s; }
.hidden-ui .hint, .hidden-ui .viewer-controls, .hidden-ui #top-bar, .hidden-ui #tag-overlay { opacity: 0; pointer-events: none; }

#tag-overlay { position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%); width: 80%; max-width: 600px; background: var(--surface); padding: 15px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: none; z-index: 101; transition: opacity 0.3s; }
#tag-overlay.show { display: block; }
#tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; max-height: 100px; overflow-y: auto; }
.tag-bubble { background: var(--accent); color: #fff; padding: 5px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; }
.tag-bubble:hover { filter: brightness(1.1); }
.tag-input { width: 100%; background: var(--bg); border: 1px solid var(--surface-hover); padding: 10px; border-radius: 8px; color: var(--text); box-sizing: border-box; margin-bottom: 10px; }
.tag-save-btn { width: 100%; background: var(--accent); color: #fff; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 600; }

#settings-modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.7); display: none; justify-content: center; align-items: center; z-index: 200; }
.settings-card { background: var(--surface); padding: 30px; border-radius: 20px; width: 400px; }
.settings-title { font-weight: 700; font-size: 20px; margin-bottom: 20px; text-align: center; }
.setting-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.setting-item label { font-weight: 500; }
input[type="range"] { width: 200px; accent-color: var(--accent); }
input[type="number"] { width: 60px; background: var(--bg); color: var(--text); border: 1px solid var(--surface-hover); padding: 5px; border-radius: 5px; text-align: center; }
.text-input { width: 100%; background: var(--bg); color: var(--text); border: 1px solid var(--surface-hover); padding: 10px; border-radius: 8px; margin-bottom: 10px; box-sizing: border-box; }
.close-modal { width: 100%; background: var(--accent); color: #fff; border: none; padding: 12px; border-radius: 12px; font-weight: 600; cursor: pointer; font-size: 16px; margin-top: 10px; }
.close-modal.danger { background: var(--danger); }
.drag-over { border: 4px dashed var(--accent) !important; box-sizing: border-box; }
.divider { border-bottom: 1px solid var(--surface-hover); margin: 20px 0; }
</style></head><body>

<div id="top-bar">
    <div class="top-left">
        <div class="logo"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent);"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> Vault</div>
        
        <!-- Vault Selector -->
        <div class="dropdown" id="vault-dropdown">
            <button class="dropbtn" onclick="toggleVaultDropdown()">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                <span id="vault-btn-text">Loading...</span>
            </button>
            <div class="dropdown-content" id="vault-content" style="min-width: 200px;">
                <div class="dropdown-item accent" onclick="createVaultPrompt()"><span>Create New Vault</span></div>
                <div class="dropdown-item danger" onclick="deleteVaultPrompt()"><span>Delete Current Vault</span></div>
            </div>
        </div>

        <div class="dropdown" id="filter-dropdown">
            <button class="dropbtn" onclick="toggleFilterDropdown()">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
                <span id="filter-btn-text">All</span>
            </button>
            <div class="dropdown-content" id="filter-content">
                <label class="dropdown-item"><input type="checkbox" value="image" checked onchange="updateFilter()"> Images</label>
                <label class="dropdown-item"><input type="checkbox" value="gif" checked onchange="updateFilter()"> GIFs</label>
                <label class="dropdown-item"><input type="checkbox" value="video" checked onchange="updateFilter()"> Videos</label>
            </div>
        </div>

        <div class="search-wrapper" id="search-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" id="search-input" class="search-input" placeholder="Search tags..." oninput="handleSearch()" onkeydown="handleSearchNav(event)" autocomplete="off">
            <div id="search-suggestions" class="suggestions-box"></div>
        </div>
    </div>
    <div class="top-right">
        <input type="file" id="file-input" multiple style="display:none;">
        <button class="icon-btn" onclick="document.getElementById('file-input').click()" title="Upload Files">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        </button>
        <button class="icon-btn" id="import-btn" onclick="importInbox()" title="Import from Inbox">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span class="badge" id="inbox-badge" style="display:none;">0</span>
        </button>
        <button class="icon-btn" onclick="toggleSettings()" title="Settings">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        </button>
        <button class="icon-btn danger" onclick="shutdownServer()" title="Shutdown App">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
        </button>
    </div>
</div>

<div id="gallery"></div>

<div id="viewer">
    <img id="media-img" src="" style="display:none;">
    <video id="media-video" src="" style="display:none;" controls></video>
    
    <div id="tag-overlay">
        <div id="tag-list"></div>
        <input type="text" id="tag-input" class="tag-input" placeholder="Enter tags separated by space or comma...">
        <button class="tag-save-btn" onclick="saveTags()">Save Tags</button>
    </div>

    <div class="viewer-controls">
        <button class="vc-btn" onclick="prevMedia()" title="Previous (A)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg></button>
        <button class="vc-btn" onclick="zoomOut()" title="Zoom Out (X)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg></button>
        <button class="vc-btn" onclick="zoomIn()" title="Zoom In (Z)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg></button>
        <button class="vc-btn" onclick="resetZoomPan()" title="Reset Zoom (C)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg></button>
        <button class="vc-btn" onclick="toggleTagOverlay()" title="Tags (T)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg></button>
        <button class="vc-btn" onclick="nextMedia()" title="Next (D)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg></button>
        <button class="vc-btn danger" onclick="deleteMedia()" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
        <button class="vc-btn" onclick="closeViewer()" title="Close (Esc)"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
    </div>
    <div class="hint">A/D: Nav | W/S: Pan | Z/X: Zoom | C: Reset | T: Tags | Space: Play/Pause | H: Hide UI | Del: Delete | Esc: Close</div>
</div>

<div id="settings-modal">
    <div class="settings-card">
        <div class="settings-title">Settings</div>
        
        <div class="setting-item"><label>Theme</label><button class="icon-btn" onclick="toggleTheme()" style="width: 60px;"><svg id="theme-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg></button></div>
        <div class="setting-item"><label>Thumbnail Size</label><input type="range" min="100" max="300" value="150" id="grid-size-slider" onchange="updateGridSize(this.value)"></div>
        <div class="setting-item"><label>Slideshow Interval (sec)</label><input type="number" min="1" max="60" value="3" id="slideshow-interval" onchange="saveSettings()"></div>
        <div class="setting-item"><label>Enable Slideshow</label><button class="icon-btn" onclick="toggleSlideshow()" id="slideshow-btn" style="width: 60px; background: var(--surface-hover);"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg></button></div>
        
        <div class="divider"></div>
        
        <div class="settings-title" style="font-size: 16px; margin-bottom: 15px;">Change Password</div>
        <input type="password" id="old-pass-input" class="text-input" placeholder="Old Password">
        <input type="password" id="new-pass-input" class="text-input" placeholder="New Password">
        <button class="close-modal" onclick="changePassword()">Apply New Password</button>
        
        <div class="divider"></div>
        
        <button class="close-modal danger" onclick="shutdownServer()">Shutdown Vault</button>
        <button class="close-modal" onclick="toggleSettings()" style="background: var(--surface-hover); margin-top: 10px;">Close Settings</button>
    </div>
</div>

<script>
let files = []; let fileTags = {}; let allTags = []; let currentIndex = 0; let scale = 1, translateX = 0, translateY = 0; 
let activeFilters = ['image', 'gif', 'video'];
let searchQuery = '';
let currentSuggestionIndex = -1;
let settings = { theme: 'dark', gridSize: 150, slideshow: false, interval: 3 }; 
let slideshowTimer = null;
let keysPressed = {};
let panAnimationId = null;

setInterval(() => { fetch('/api/ping', { method: 'POST' }).catch(err => console.error("Ping failed", err)); }, 5000);

function startPanLoop() {
    if (panAnimationId) return;
    const img = document.getElementById('media-img');
    const vid = document.getElementById('media-video');
    img.style.transition = 'none'; vid.style.transition = 'none';
    function loop() {
        if (scale <= 1.1) { stopPanLoop(); return; }
        const speed = 20;
        if (keysPressed['KeyW']) translateY += speed;
        if (keysPressed['KeyS']) translateY -= speed;
        if (keysPressed['KeyA']) translateX += speed;
        if (keysPressed['KeyD']) translateX -= speed;
        updateTransform();
        panAnimationId = requestAnimationFrame(loop);
    }
    panAnimationId = requestAnimationFrame(loop);
}

function stopPanLoop() {
    if (panAnimationId) { cancelAnimationFrame(panAnimationId); panAnimationId = null; }
    const img = document.getElementById('media-img');
    const vid = document.getElementById('media-video');
    img.style.transition = 'transform 0.1s ease-out'; vid.style.transition = 'transform 0.1s ease-out';
}

function resetZoomPan() { scale = 1; translateX = 0; translateY = 0; updateTransform(); stopPanLoop(); }
function loadSettings() { const s = localStorage.getItem('vaultSettings'); if (s) settings = JSON.parse(s); applySettings(); }
function saveSettings() { settings.interval = parseInt(document.getElementById('slideshow-interval').value) || 3; localStorage.setItem('vaultSettings', JSON.stringify(settings)); }
function applySettings() {
    document.body.classList.toggle('light-theme', settings.theme === 'light');
    document.documentElement.style.setProperty('--grid-size', settings.gridSize + 'px');
    document.getElementById('grid-size-slider').value = settings.gridSize;
    document.getElementById('slideshow-interval').value = settings.interval;
    const ssBtn = document.getElementById('slideshow-btn'); ssBtn.style.background = settings.slideshow ? 'var(--accent)' : 'var(--surface-hover)'; ssBtn.style.color = settings.slideshow ? '#fff' : 'var(--text)';
    const ti = document.getElementById('theme-icon');
    if (settings.theme === 'light') ti.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    else ti.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
}
function toggleTheme() { settings.theme = settings.theme === 'dark' ? 'light' : 'dark'; saveSettings(); applySettings(); }
function toggleSlideshow() { settings.slideshow = !settings.slideshow; saveSettings(); applySettings(); handleSlideshow(); }
function updateGridSize(v) { settings.gridSize = parseInt(v); saveSettings(); applySettings(); }

function toggleVaultDropdown() {
    document.getElementById("vault-content").classList.toggle("show");
    document.getElementById("filter-content").classList.remove("show");
    document.getElementById("search-suggestions").classList.remove("show");
}
function toggleFilterDropdown() {
    document.getElementById("filter-content").classList.toggle("show");
    document.getElementById("vault-content").classList.remove("show");
    document.getElementById("search-suggestions").classList.remove("show");
}
window.onclick = function(event) {
    if (!event.target.matches('.dropbtn') && !event.target.closest('#filter-dropdown') && !event.target.closest('#vault-dropdown')) {
        document.getElementById("filter-content").classList.remove('show');
        document.getElementById("vault-content").classList.remove('show');
    }
    if (!event.target.closest('#search-wrapper')) {
        document.getElementById('search-suggestions').classList.remove('show');
    }
}

function renderVaultsDropdown(vaults, currentVaultId) {
    const content = document.getElementById('vault-content');
    const currentVault = vaults.find(v => v.id === currentVaultId);
    document.getElementById('vault-btn-text').innerText = currentVault ? currentVault.name : 'No Vault';
    
    // Remove old vault items
    const oldItems = content.querySelectorAll('.vault-select-item');
    oldItems.forEach(el => el.remove());
    
    // Insert vaults at the top
    vaults.forEach(v => {
        const el = document.createElement('div');
        el.className = 'dropdown-item vault-select-item';
        if (v.id === currentVaultId) el.style.fontWeight = 'bold';
        el.innerHTML = `<span style="flex:1; overflow:hidden; text-overflow:ellipsis;">${v.name}</span>`;
        if (v.id === currentVaultId) el.innerHTML += '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        el.onclick = () => switchVault(v.id);
        content.insertBefore(el, content.firstChild);
    });
}

function switchVault(id) {
    fetch('/api/vaults/switch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id})
    }).then(r => r.json()).then(d => {
        if(d.success) {
            document.getElementById('search-input').value = '';
            searchQuery = '';
            loadVaults();
            document.getElementById('vault-content').classList.remove('show');
        }
    });
}

function createVaultPrompt() {
    const name = prompt("Enter name for the new vault:");
    if (!name) return;
    fetch('/api/vaults/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name})
    }).then(r => r.json()).then(d => {
        if(d.success) {
            document.getElementById('search-input').value = '';
            searchQuery = '';
            loadVaults();
            document.getElementById('vault-content').classList.remove('show');
        }
    });
}

function deleteVaultPrompt() {
    if(!confirm("Are you sure you want to permanently delete the current vault and all its files?")) return;
    fetch('/api/vaults/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: window.currentVaultId})
    }).then(r => r.json()).then(d => {
        if(d.success) {
            document.getElementById('search-input').value = '';
            searchQuery = '';
            loadVaults();
            document.getElementById('vault-content').classList.remove('show');
        }
    });
}

function loadVaults() {
    fetch('/api/vaults')
    .then(r => r.json())
    .then(data => {
        window.currentVaultId = data.current;
        renderVaultsDropdown(data.vaults, data.current);
        loadData();
    });
}

function updateFilter() {
    const checkboxes = document.querySelectorAll('#filter-content input[type="checkbox"]:checked');
    activeFilters = Array.from(checkboxes).map(c => c.value);
    const textEl = document.getElementById('filter-btn-text');
    if (activeFilters.length === 3) textEl.innerText = 'All';
    else if (activeFilters.length === 0) textEl.innerText = 'None';
    else textEl.innerText = activeFilters.map(f => f.charAt(0).toUpperCase() + f.slice(1)).join(" + ");
    renderGallery();
}

function calculateTagStats() {
    const counts = {};
    Object.values(fileTags).forEach(tags => {
        tags.forEach(t => {
            if (!counts[t]) counts[t] = 0;
            counts[t]++;
        });
    });
    allTags = Object.keys(counts).map(tag => ({ tag: tag, count: counts[tag] }));
    allTags.sort((a, b) => b.count - a.count);
}

function handleSearch() {
    searchQuery = document.getElementById('search-input').value.toLowerCase().trim();
    renderGallery();
    showSuggestions();
}

function showSuggestions() {
    const box = document.getElementById('search-suggestions');
    if (!searchQuery) { box.classList.remove('show'); return; }
    const terms = searchQuery.split(/[\s,]+/).filter(t => t.length > 0);
    const lastTerm = terms[terms.length - 1] || searchQuery;
    const matches = allTags.filter(t => t.tag.toLowerCase().includes(lastTerm)).slice(0, 5);
    if (matches.length === 0) { box.classList.remove('show'); return; }
    box.innerHTML = '';
    matches.forEach((m, idx) => {
        const el = document.createElement('div');
        el.className = 'suggestion-item';
        el.innerHTML = `<span>${m.tag}</span><span class="suggestion-count">${m.count}</span>`;
        el.onclick = () => selectSuggestion(m.tag);
        box.appendChild(el);
    });
    currentSuggestionIndex = -1;
    box.classList.add('show');
}

function selectSuggestion(tag) {
    let input = document.getElementById('search-input');
    let terms = input.value.trim().split(/[\s,]+/).filter(t => t.length > 0);
    if (terms.length > 0) terms[terms.length - 1] = tag;
    else terms.push(tag);
    input.value = terms.join(' ') + ' ';
    handleSearch();
    input.focus();
}

function handleSearchNav(e) {
    const box = document.getElementById('search-suggestions');
    if (!box.classList.contains('show')) return;
    const items = box.querySelectorAll('.suggestion-item');
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        currentSuggestionIndex = Math.min(currentSuggestionIndex + 1, items.length - 1);
        updateSuggestionHighlight(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        currentSuggestionIndex = Math.max(currentSuggestionIndex - 1, -1);
        updateSuggestionHighlight(items);
    } else if (e.key === 'Enter' && currentSuggestionIndex >= 0) {
        e.preventDefault();
        if (items[currentSuggestionIndex]) items[currentSuggestionIndex].click();
    } else if (e.key === 'Escape') {
        box.classList.remove('show');
    }
}

function updateSuggestionHighlight(items) {
    items.forEach((item, idx) => item.classList.toggle('active', idx === currentSuggestionIndex));
    if (currentSuggestionIndex >= 0 && items[currentSuggestionIndex]) {
        items[currentSuggestionIndex].scrollIntoView({ block: 'nearest' });
    }
}

function loadData() {
    fetch('/api/files?t=' + Date.now())
    .then(r => r.json())
    .then(data => {
        files = data.files; 
        fileTags = data.tags || {};
        calculateTagStats();
        const b = document.getElementById('inbox-badge');
        if (data.inbox_count > 0) { b.style.display = 'flex'; b.innerText = data.inbox_count; } else { b.style.display = 'none'; }
        renderGallery();
    });
}

function getMediaType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (['mp4', 'mkv', 'webm', 'mov'].includes(ext)) return 'video';
    if (ext === 'gif') return 'gif';
    return 'image';
}

function renderGallery() {
    const g = document.getElementById('gallery'); g.innerHTML = '';
    const searchTerms = searchQuery.split(/[\s,]+/).filter(t => t.length > 0);
    
    files.forEach((file, index) => {
        const type = getMediaType(file);
        if (!activeFilters.includes(type)) return;
        
        const tags = (fileTags[file] || []).map(t => t.toLowerCase());
        const fileStr = (file + " " + tags.join(" ")).toLowerCase();
        
        if (searchTerms.length > 0) {
            const matches = searchTerms.every(term => fileStr.includes(term));
            if (!matches) return;
        }
        
        const el = document.createElement('img'); 
        el.className = 'media-item';
        el.onclick = () => openViewer(index); 
        el.src = '/thumbnail/' + encodeURIComponent(file) + '?t=' + Date.now();
        el.loading = 'lazy'; 
        el.onerror = function() { this.style.opacity = '0.1'; };
        g.appendChild(el);
    });
}

function uploadFiles(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) formData.append('files[]', files[i]);
    fetch('/api/upload', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(d => { if(d.success) { alert("Uploaded: " + d.uploaded); loadData(); } });
}

document.getElementById('file-input').addEventListener('change', function() {
    if(this.files.length > 0) uploadFiles(this.files);
    this.value = "";
});

const gallery = document.getElementById('gallery');
gallery.addEventListener('dragover', e => { e.preventDefault(); gallery.classList.add('drag-over'); });
gallery.addEventListener('dragleave', e => { gallery.classList.remove('drag-over'); });
gallery.addEventListener('drop', e => {
    e.preventDefault(); gallery.classList.remove('drag-over');
    if(e.dataTransfer.files.length > 0) uploadFiles(e.dataTransfer.files);
});

function importInbox() { if(!confirm("Encrypt and import files from inbox to vault?")) return; fetch('/api/import', {method: 'POST'}).then(r => r.json()).then(d => { if(d.success) { alert("Imported: " + d.imported); loadData(); } }); }
function openViewer(i) { currentIndex = i; document.getElementById('gallery').style.display = 'none'; document.getElementById('viewer').style.display = 'flex'; showMedia(); }
function closeViewer() { 
    const v = document.getElementById('media-video'); 
    v.pause(); v.src = ""; 
    document.getElementById('viewer').style.display = 'none'; 
    document.getElementById('gallery').style.display = 'grid'; 
    document.body.classList.remove('hidden-ui'); 
    document.getElementById('tag-overlay').classList.remove('show'); 
    if (slideshowTimer) clearTimeout(slideshowTimer); 
    stopPanLoop(); 
}
function getCurrentType() { return getMediaType(files[currentIndex]); }
function showMedia() {
    if (currentIndex < 0) currentIndex = files.length - 1; if (currentIndex >= files.length) currentIndex = 0;
    const file = files[currentIndex]; const type = getCurrentType(); const img = document.getElementById('media-img'); const vid = document.getElementById('media-video');
    resetZoomPan();
    document.getElementById('tag-overlay').classList.remove('show');
    
    if (type === 'video') { img.style.display = 'none'; vid.style.display = 'block'; vid.src = '/media/' + encodeURIComponent(file); vid.play(); vid.onended = () => handleSlideshow(true); } 
    else { vid.pause(); vid.style.display = 'none'; vid.src = ""; img.style.display = 'block'; img.src = '/media/' + encodeURIComponent(file); handleSlideshow(); }
    
    const tags = fileTags[file] || [];
    document.getElementById('tag-input').value = tags.join(', ');
    renderTagList(tags);
}
function handleSlideshow(vidEnded = false) { if (slideshowTimer) { clearTimeout(slideshowTimer); slideshowTimer = null; } if (settings.slideshow && document.getElementById('viewer').style.display === 'flex') { if (getCurrentType() === 'video' && !vidEnded) return; slideshowTimer = setTimeout(() => nextMedia(), settings.interval * 1000); } }
function prevMedia() { currentIndex--; showMedia(); } function nextMedia() { currentIndex++; showMedia(); }
function zoomIn() { scale *= 1.2; updateTransform(); } 
function zoomOut() { scale /= 1.2; if (scale < 1.1) { resetZoomPan(); } else { updateTransform(); } }
function deleteMedia() { if(!confirm("Permanently delete this file?")) return; fetch('/api/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename: files[currentIndex]}) }).then(r => r.json()).then(d => { if(d.success) { files.splice(currentIndex, 1); showMedia(); loadData(); } }); }

function updateTransform() {
    const img = document.getElementById('media-img');
    const vid = document.getElementById('media-video');
    const transformStr = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    if (img.style.display === 'block') img.style.transform = transformStr;
    if (vid.style.display === 'block') vid.style.transform = transformStr;
}

function toggleSettings() { document.getElementById('settings-modal').style.display = document.getElementById('settings-modal').style.display === 'flex' ? 'none' : 'flex'; }

function changePassword() {
    const oldPass = document.getElementById('old-pass-input').value;
    const newPass = document.getElementById('new-pass-input').value;
    if (!oldPass || !newPass) { alert("Please fill both fields"); return; }
    fetch('/api/change_password', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({old_pass: oldPass, new_pass: newPass}) })
    .then(r => r.json())
    .then(d => {
        if(d.success) {
            alert(d.message);
            document.getElementById('old-pass-input').value = '';
            document.getElementById('new-pass-input').value = '';
        } else {
            alert("Error: " + d.error);
        }
    });
}

function shutdownServer() {
    if(!confirm("Shutdown the application?")) return;
    fetch('/api/shutdown', { method: 'POST' }).then(() => {
        document.body.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh;color:white;font-family:sans-serif;"><h2>Application has been shut down. You can close this window.</h2></div>';
    });
}

function toggleTagOverlay() { document.getElementById('tag-overlay').classList.toggle('show'); }
function renderTagList(tags) {
    const list = document.getElementById('tag-list');
    list.innerHTML = '';
    if (tags.length === 0) { list.innerHTML = '<span style="color: var(--text-dim); font-size: 12px;">No tags yet</span>'; return; }
    tags.forEach(tag => {
        const el = document.createElement('span');
        el.className = 'tag-bubble';
        el.innerText = tag;
        el.onclick = () => {
            document.getElementById('search-input').value = tag;
            handleSearch();
            closeViewer();
        };
        list.appendChild(el);
    });
}
function saveTags() {
    const file = files[currentIndex];
    const inputVal = document.getElementById('tag-input').value;
    const tags = inputVal.split(/[\s,]+/).map(t => t.trim()).filter(t => t.length > 0);
    fileTags[file] = tags;
    fetch('/api/tags/update', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename: file, tags: tags}) })
    .then(r => r.json())
    .then(d => {
        if(d.success) {
            renderTagList(tags);
            document.getElementById('tag-input').value = tags.join(', ');
            calculateTagStats(); 
            alert("Tags saved!");
        }
    });
}

document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (document.getElementById('settings-modal').style.display === 'flex') return;
    if (document.getElementById('viewer').style.display !== 'flex') return;
    
    keysPressed[e.code] = true; const c = e.code; const v = document.getElementById('media-video'); const isVid = v.style.display === 'block';
    switch(c) {
        case 'Escape': closeViewer(); break; 
        case 'KeyH': document.body.classList.toggle('hidden-ui'); break;
        case 'KeyT': toggleTagOverlay(); break;
        case 'Space': if (isVid) { e.preventDefault(); v.paused ? v.play() : v.pause(); } break;
        case 'KeyC': resetZoomPan(); break;
        case 'KeyZ': zoomIn(); break; case 'KeyX': zoomOut(); break; case 'Delete': deleteMedia(); break;
    }
    if (scale > 1.1) {
        if (['KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(c)) { e.preventDefault(); if (!panAnimationId) startPanLoop(); }
    } else {
        if (c === 'KeyA') prevMedia();
        if (c === 'KeyD') nextMedia();
    }
});

document.addEventListener('keyup', (e) => {
    keysPressed[e.code] = false;
    if (!keysPressed['KeyW'] && !keysPressed['KeyA'] && !keysPressed['KeyS'] && !keysPressed['KeyD']) stopPanLoop();
});

loadSettings(); loadVaults();
</script>
</body></html>
'''

# ================== LAUNCHER & HEARTBEAT ==================
def monitor_heartbeat():
    global LAST_PING
    while True:
        time.sleep(5)
        if time.time() - LAST_PING > 15:
            print("Browser closed or inactive. Shutting down...")
            os.kill(os.getpid(), signal.SIGINT)
            break

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

def start_server():
    os.makedirs(INBOX_FOLDER, exist_ok=True)
    os.makedirs(VAULTS_DIR, exist_ok=True)
    
    t = Thread(target=monitor_heartbeat, daemon=True)
    t.start()
    
    Timer(1.5, open_browser).start()
    app.run(debug=False, port=5000, use_reloader=False)

if __name__ == "__main__":
    start_server()