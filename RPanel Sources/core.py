# core.py — движок хранилища: шифрование, файлы, метаданные, кэши
import os
import sys
import io
import json
import time
import base64
import shutil
import hashlib
import tempfile
import threading
import zipfile

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from PIL import Image, ImageOps

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# При сборке в exe данные должны лежать рядом с exe, а не во временном каталоге PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INBOX_FOLDER = os.path.join(BASE_DIR, "inbox")
VAULTS_DIR = os.path.join(BASE_DIR, "vaults")
SALT_FILE = os.path.join(BASE_DIR, "salt.bin")
MASTER_KEY_FILE = os.path.join(BASE_DIR, "master.key.enc")
VAULT_REGISTRY_FILE = os.path.join(BASE_DIR, "vaults.enc")
R34_CONFIG_FILE = os.path.join(BASE_DIR, "r34_config.json")

EXPORT_DIR = os.path.join(tempfile.gettempdir(), "rpanel_export")

MEDIA_EXTS = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".bmp": "image", ".webp": "image",
    ".gif": "gif",
    ".mp4": "video", ".mkv": "video", ".webm": "video", ".mov": "video",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio", ".flac": "audio",
}
ALLOWED_EXTENSIONS = tuple(MEDIA_EXTS)
META_FILES = {"meta.enc", "tags.enc", "hashes.enc"}

THUMB_SIZE = 512
GIF_THUMB_MAX = 3 * 1024 * 1024
AUTOLOCK_MINUTES = 15

CURRENT_KEY = None
IS_LOCKED = True
LAST_ACTIVITY = time.time()

_lock = threading.RLock()
_failed = []


# ---------------- криптография ----------------
def get_salt():
    if not os.path.exists(SALT_FILE):
        with open(SALT_FILE, "wb") as f:
            f.write(os.urandom(16))
    with open(SALT_FILE, "rb") as f:
        return f.read()


def derive_key(password):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=get_salt(), iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def vault_exists():
    return os.path.exists(MASTER_KEY_FILE)


def fernet():
    return Fernet(CURRENT_KEY) if CURRENT_KEY else None


def unlock(password):
    """Создаёт хранилище при первом запуске или снимает блокировку."""
    global CURRENT_KEY, IS_LOCKED
    if not vault_exists():
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        master = Fernet.generate_key()
        with open(MASTER_KEY_FILE, "wb") as f:
            f.write(Fernet(derive_key(password)).encrypt(master))
        with _lock:
            CURRENT_KEY = master
            IS_LOCKED = False
        touch()
        return True, None
    try:
        with open(MASTER_KEY_FILE, "rb") as f:
            master = Fernet(derive_key(password)).decrypt(f.read())
    except InvalidToken:
        return False, "Wrong password"
    with _lock:
        CURRENT_KEY = master
        IS_LOCKED = False
    touch()
    return True, None


def lock():
    global CURRENT_KEY, IS_LOCKED
    with _lock:
        CURRENT_KEY = None
        IS_LOCKED = True
    purge_media_cache()


def change_password(old, new):
    if not vault_exists():
        return False, "Vault is not initialized yet"
    if len(new) < 6:
        return False, "New password must be at least 6 characters"
    try:
        with open(MASTER_KEY_FILE, "rb") as f:
            master = Fernet(derive_key(old)).decrypt(f.read())
    except InvalidToken:
        return False, "Current password is wrong"
    with open(MASTER_KEY_FILE, "wb") as f:
        f.write(Fernet(derive_key(new)).encrypt(master))
    return True, "Password updated"


def touch():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()


def login_blocked():
    with _lock:
        now = time.time()
        while _failed and now - _failed[0] > 600:
            _failed.pop(0)
        return len(_failed) >= 5 and now - _failed[-1] < 60


def record_failure():
    with _lock:
        _failed.append(time.time())


def clear_failures():
    with _lock:
        _failed.clear()


# ---------------- имена ----------------
def sanitize_filename(name):
    name = os.path.basename(str(name).replace("\\", "/")).strip().lstrip(".")
    name = "".join(c for c in name if c not in '<>:"|?*' and ord(c) >= 32)
    return name[:160]


def valid_name(name):
    return (bool(name) and len(name) <= 200 and "/" not in name
            and "\\" not in name and ".." not in name)


# ---------------- хранилища ----------------
def vault_path(vault_id, *parts):
    return os.path.join(VAULTS_DIR, vault_id, *parts)


def get_vaults():
    if IS_LOCKED or not CURRENT_KEY or not os.path.exists(VAULT_REGISTRY_FILE):
        return []
    try:
        with open(VAULT_REGISTRY_FILE, "rb") as f:
            return json.loads(fernet().decrypt(f.read()))
    except Exception:
        return []


def save_vaults(vaults):
    if not CURRENT_KEY:
        return
    with open(VAULT_REGISTRY_FILE, "wb") as f:
        f.write(fernet().encrypt(json.dumps(vaults).encode()))


def ensure_vault_dirs(vault_id):
    os.makedirs(vault_path(vault_id), exist_ok=True)
    os.makedirs(vault_path(vault_id, "thumbs"), exist_ok=True)
    os.makedirs(vault_path(vault_id, "trash"), exist_ok=True)


def ensure_default_vault():
    vaults = get_vaults()
    if not vaults:
        vid = os.urandom(8).hex()
        vaults = [{"id": vid, "name": "Default"}]
        save_vaults(vaults)
        ensure_vault_dirs(vid)
    return vaults


def create_vault(name):
    name = str(name).strip()[:60] or "Vault"
    vaults = get_vaults()
    vid = os.urandom(8).hex()
    vaults.append({"id": vid, "name": name})
    save_vaults(vaults)
    ensure_vault_dirs(vid)
    return vid


def rename_vault(vault_id, name):
    name = str(name).strip()[:60]
    if not name:
        return False
    vaults = get_vaults()
    for v in vaults:
        if v["id"] == vault_id:
            v["name"] = name
            save_vaults(vaults)
            return True
    return False


def delete_vault(vault_id):
    vaults = get_vaults()
    remaining = [v for v in vaults if v["id"] != vault_id]
    if len(remaining) == len(vaults):
        return False
    if os.path.exists(vault_path(vault_id)):
        shutil.rmtree(vault_path(vault_id), ignore_errors=True)
    save_vaults(remaining)
    if remaining:
        return remaining[0]["id"]
    vid = os.urandom(8).hex()
    save_vaults([{"id": vid, "name": "Default"}])
    ensure_vault_dirs(vid)
    return vid


def count_files(vault_id, trash=False):
    folder = vault_path(vault_id, "trash") if trash else vault_path(vault_id)
    if not os.path.isdir(folder):
        return 0
    n = 0
    for f in os.listdir(folder):
        if f.endswith(".enc") and f not in META_FILES:
            if os.path.splitext(f[:-4])[1].lower() in MEDIA_EXTS:
                n += 1
    return n


def vaults_with_counts():
    vaults = get_vaults()
    for v in vaults:
        v["count"] = count_files(v["id"])
    return vaults


# ---------------- метаданные (теги/избранное/дата) ----------------
def load_meta(vault_id):
    meta = {"files": {}}
    path = vault_path(vault_id, "meta.enc")
    if CURRENT_KEY and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                meta = json.loads(fernet().decrypt(f.read()))
            if not isinstance(meta.get("files"), dict):
                meta = {"files": {}}
        except Exception:
            meta = {"files": {}}
    legacy = vault_path(vault_id, "tags.enc")
    if CURRENT_KEY and os.path.exists(legacy):
        try:  # миграция старого формата tags.enc -> meta.enc
            with open(legacy, "rb") as f:
                old = json.loads(fernet().decrypt(f.read()))
            for name, tags in old.items():
                if name not in meta["files"]:
                    meta["files"][name] = {"tags": tags if isinstance(tags, list) else [],
                                           "fav": False}
            save_meta(vault_id, meta)
            os.remove(legacy)
        except Exception:
            pass
    return meta


def save_meta(vault_id, meta):
    if not CURRENT_KEY:
        return
    with open(vault_path(vault_id, "meta.enc"), "wb") as f:
        f.write(fernet().encrypt(json.dumps(meta).encode()))


def update_meta(vault_id, name, tags=None, fav=None):
    meta = load_meta(vault_id)
    m = meta["files"].setdefault(name, {"tags": [], "fav": False, "added": time.time()})
    if tags is not None:
        m["tags"] = [str(t).strip() for t in tags if str(t).strip()]
    if fav is not None:
        m["fav"] = bool(fav)
    save_meta(vault_id, meta)


def bulk_update(vault_id, names, add_tags=None, remove_tags=None, fav=None):
    meta = load_meta(vault_id)
    for n in names:
        m = meta["files"].setdefault(n, {"tags": [], "fav": False, "added": time.time()})
        if add_tags:
            m["tags"] = sorted(set(m.get("tags") or []) | set(add_tags))
        if remove_tags:
            m["tags"] = sorted(set(m.get("tags") or []) - set(remove_tags))
        if fav is not None:
            m["fav"] = bool(fav)
    save_meta(vault_id, meta)


# ---------------- индекс хэшей (антидубликаты) ----------------
def load_hashes(vault_id):
    path = vault_path(vault_id, "hashes.enc")
    if CURRENT_KEY and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                h = json.loads(fernet().decrypt(f.read()))
            if isinstance(h, dict):
                return h
        except Exception:
            pass
    return {}


def save_hashes(vault_id, hashes):
    if not CURRENT_KEY:
        return
    with open(vault_path(vault_id, "hashes.enc"), "wb") as f:
        f.write(fernet().encrypt(json.dumps(hashes).encode()))


# ---------------- файлы ----------------
def list_files(vault_id, trash=False):
    folder = vault_path(vault_id, "trash") if trash else vault_path(vault_id)
    if not os.path.isdir(folder):
        return []
    meta = load_meta(vault_id)
    out = []
    for f in os.listdir(folder):
        if not f.endswith(".enc") or f in META_FILES:
            continue
        name = f[:-4]
        mtype = MEDIA_EXTS.get(os.path.splitext(name)[1].lower())
        if not mtype:
            continue
        try:
            mtime = os.path.getmtime(os.path.join(folder, f))
        except OSError:
            mtime = 0
        m = meta["files"].get(name) or {}
        out.append({"name": name, "type": mtype, "tags": m.get("tags") or [],
                    "fav": bool(m.get("fav")), "added": m.get("added") or mtime})
    return out


def add_media(vault_id, filename, data, tags=None, fav=False):
    """Шифрует и сохраняет файл. Возвращает dict со статусом."""
    digest = hashlib.sha256(data).hexdigest()
    filename = sanitize_filename(filename)
    if not filename:
        return {"status": "error"}
    base, ext = os.path.splitext(filename)
    if not base:
        filename = "file" + ext
        base = "file"
    hashes = load_hashes(vault_id)
    existing = hashes.get(digest)
    if existing:
        in_main = os.path.exists(vault_path(vault_id, existing + ".enc"))
        in_trash = os.path.exists(vault_path(vault_id, "trash", existing + ".enc"))
        if in_main or in_trash:
            return {"status": "duplicate", "name": existing,
                    "in_trash": in_trash and not in_main}
    ensure_vault_dirs(vault_id)
    final, n = filename, 1
    while (os.path.exists(vault_path(vault_id, final + ".enc")) or
           os.path.exists(vault_path(vault_id, "trash", final + ".enc"))):
        n += 1
        final = "%s (%d)%s" % (base, n, ext)
    with open(vault_path(vault_id, final + ".enc"), "wb") as f:
        f.write(fernet().encrypt(data))
    hashes[digest] = final
    save_hashes(vault_id, hashes)
    meta = load_meta(vault_id)
    meta["files"][final] = {"tags": [str(t) for t in (tags or [])],
                            "fav": bool(fav), "added": time.time()}
    save_meta(vault_id, meta)
    return {"status": "ok", "name": final}


def trash_file(vault_id, name):
    src = vault_path(vault_id, name + ".enc")
    if not os.path.exists(src):
        return False
    os.makedirs(vault_path(vault_id, "trash"), exist_ok=True)
    base, ext = os.path.splitext(name)
    dst, n = os.path.join(vault_path(vault_id, "trash"), name + ".enc"), 1
    while os.path.exists(dst):
        dst = os.path.join(vault_path(vault_id, "trash"), "%s (%d)%s.enc" % (base, n, ext))
        n += 1
    shutil.move(src, dst)
    drop_media_cache(vault_id, name)
    return True


def restore_file(vault_id, name):
    src = vault_path(vault_id, "trash", name + ".enc")
    if not os.path.exists(src):
        return False
    base, ext = os.path.splitext(name)
    final, n = name, 1
    while os.path.exists(vault_path(vault_id, final + ".enc")):
        final = "%s (%d)%s" % (base, n, ext)
        n += 1
    shutil.move(src, vault_path(vault_id, final + ".enc"))
    if final != name:
        meta = load_meta(vault_id)
        m = meta["files"].pop(name, None)
        if m:
            meta["files"][final] = m
            save_meta(vault_id, meta)
    return True


def purge_file(vault_id, name):
    """Безвозвратно удаляет файл из корзины."""
    path = vault_path(vault_id, "trash", name + ".enc")
    removed = False
    if os.path.exists(path):
        os.remove(path)
        removed = True
    _drop_thumb(vault_id, name)
    drop_media_cache(vault_id, name)
    meta = load_meta(vault_id)
    if name in meta["files"]:
        meta["files"].pop(name)
        save_meta(vault_id, meta)
    hashes = load_hashes(vault_id)
    for h, n in list(hashes.items()):
        if n == name:
            del hashes[h]
            save_hashes(vault_id, hashes)
            break
    return removed


def list_trash_names(vault_id):
    folder = vault_path(vault_id, "trash")
    if not os.path.isdir(folder):
        return []
    return [f[:-4] for f in os.listdir(folder)
            if f.endswith(".enc") and os.path.splitext(f[:-4])[1].lower() in MEDIA_EXTS]


def list_vault_names(vault_id):
    folder = vault_path(vault_id)
    if not os.path.isdir(folder):
        return []
    return [f[:-4] for f in os.listdir(folder)
            if f.endswith(".enc") and f not in META_FILES
            and os.path.splitext(f[:-4])[1].lower() in MEDIA_EXTS]
def get_stats(vault_id):
    counts = {"image": 0, "gif": 0, "video": 0, "audio": 0}
    total = 0
    folder = vault_path(vault_id)
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if not f.endswith(".enc") or f in META_FILES:
                continue
            mtype = MEDIA_EXTS.get(os.path.splitext(f[:-4])[1].lower())
            if not mtype:
                continue
            counts[mtype] += 1
            try:
                total += os.path.getsize(os.path.join(folder, f))
            except OSError:
                pass
    return {"counts": counts, "files": sum(counts.values()),
            "total": total, "trash": count_files(vault_id, trash=True)}


def _cleanup_exports(max_age=3600):
    try:
        now = time.time()
        for f in os.listdir(EXPORT_DIR):
            p = os.path.join(EXPORT_DIR, f)
            try:
                if now - os.path.getmtime(p) > max_age:
                    os.remove(p)
            except OSError:
                pass
    except OSError:
        pass


def export_vault_zip(vault_id, include_trash=False):
    """Расшифровывает все медиа хранилища и упаковывает в ZIP. Возвращает путь."""
    fer = fernet()
    if not fer:
        return None
    os.makedirs(EXPORT_DIR, exist_ok=True)
    _cleanup_exports()
    fd, tmp = tempfile.mkstemp(dir=EXPORT_DIR, suffix=".zip")
    os.close(fd)
    meta = load_meta(vault_id)
    folders = [("", vault_path(vault_id))]
    if include_trash:
        folders.append(("trash/", vault_path(vault_id, "trash")))
    used = set()

    def unique_name(name):
        base, ext = os.path.splitext(name)
        final, n = name, 1
        while final.lower() in used:
            n += 1
            final = "%s (%d)%s" % (base, n, ext)
        used.add(final.lower())
        return final

    meta_out = {}
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
        for sub, folder in folders:
            if not os.path.isdir(folder):
                continue
            for f in sorted(os.listdir(folder)):
                if not f.endswith(".enc") or f in META_FILES:
                    continue
                name = f[:-4]
                if os.path.splitext(name)[1].lower() not in MEDIA_EXTS:
                    continue
                try:
                    with open(os.path.join(folder, f), "rb") as fh:
                        data = fer.decrypt(fh.read())
                except Exception:
                    continue
                z.writestr(sub + unique_name(name), data)
                m = meta["files"].get(name)
                if m:
                    meta_out[sub + name] = {"tags": m.get("tags") or [],
                                            "fav": bool(m.get("fav"))}
        if meta_out:
            z.writestr("metadata.json",
                       json.dumps(meta_out, ensure_ascii=False, indent=2))
    return tmp
# ---------------- inbox ----------------
def list_inbox():
    if not os.path.isdir(INBOX_FOLDER):
        return []
    return sorted(f for f in os.listdir(INBOX_FOLDER)
                  if os.path.isfile(os.path.join(INBOX_FOLDER, f))
                  and os.path.splitext(f)[1].lower() in MEDIA_EXTS)


def import_inbox(vault_id):
    added, dups = 0, 0
    for f in list_inbox():
        path = os.path.join(INBOX_FOLDER, f)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        res = add_media(vault_id, f, data)
        if res["status"] in ("ok", "duplicate"):
            try:
                os.remove(path)
            except OSError:
                pass
            if res["status"] == "ok":
                added += 1
            else:
                dups += 1
    return added, dups


# ---------------- r34 конфиг ----------------
def load_r34_config():
    try:
        with open(R34_CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_r34_config(api_key, user_id):
    try:
        with open(R34_CONFIG_FILE, "w") as f:
            json.dump({"api_key": api_key or "", "user_id": user_id or ""}, f)
    except OSError:
        pass


# ---------------- превью (с зашифрованным кэшем) ----------------
def _thumb_cache_path(vault_id, name):
    return os.path.join(vault_path(vault_id, "thumbs"),
                        hashlib.sha1(name.encode("utf-8")).hexdigest()[:24] + ".tenc")


def _drop_thumb(vault_id, name):
    try:
        os.remove(_thumb_cache_path(vault_id, name))
    except OSError:
        pass


def get_thumbnail(vault_id, name):
    fer = fernet()
    if not fer:
        return None
    cache = _thumb_cache_path(vault_id, name)
    if os.path.exists(cache):
        try:
            with open(cache, "rb") as f:
                return fer.decrypt(f.read())
        except InvalidToken:
            _drop_thumb(vault_id, name)
    enc_path = vault_path(vault_id, name + ".enc")
    if not os.path.exists(enc_path):
        enc_path = vault_path(vault_id, "trash", name + ".enc")
    if not os.path.exists(enc_path):
        return None
    try:
        with open(enc_path, "rb") as f:
            data = fer.decrypt(f.read())
    except InvalidToken:
        return None
    ext = os.path.splitext(name)[1].lower()
    mtype = MEDIA_EXTS.get(ext)
    out = None
    if mtype == "gif" and len(data) <= GIF_THUMB_MAX:
        out = data  # анимированное превью
    elif mtype != "audio":
        out = _make_thumb(data, ext, mtype)
    if out is not None:
        try:
            os.makedirs(vault_path(vault_id, "thumbs"), exist_ok=True)
            with open(cache, "wb") as f:
                f.write(fer.encrypt(out))
        except OSError:
            pass
    return out


def _make_thumb(data, ext, mtype):
    try:
        if mtype == "video":
            if not HAS_CV2:
                return None
            fd, tmp = tempfile.mkstemp(suffix=ext or ".mp4")
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            try:
                cap = cv2.VideoCapture(tmp)
                total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                if total > 3:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, total * 0.1)
                ok, frame = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = cap.read()
                cap.release()
                if not ok:
                    return None
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        else:
            img = Image.open(io.BytesIO(data))
            img = ImageOps.exif_transpose(img)
            if getattr(img, "is_animated", False):
                img.seek(0)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.thumbnail((THUMB_SIZE, THUMB_SIZE))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return None


# ---------------- кэш расшифрованных медиа (для стриминга) ----------------
_media_cache = {}
_media_lock = threading.Lock()
MEDIA_TTL = 600
MEDIA_MAX = 1536 * 1024 * 1024


def get_media_temp(vault_id, name):
    key = (vault_id, name)
    with _media_lock:
        entry = _media_cache.get(key)
        if entry and os.path.exists(entry["path"]):
            entry["last"] = time.time()
            return entry["path"]
    enc_path = vault_path(vault_id, name + ".enc")
    if not os.path.exists(enc_path):
        enc_path = vault_path(vault_id, "trash", name + ".enc")
    if not os.path.exists(enc_path):
        return None
    fer = fernet()
    if not fer:
        return None
    with _media_lock:
        entry = _media_cache.get(key)
        if entry and os.path.exists(entry["path"]):
            entry["last"] = time.time()
            return entry["path"]
        try:
            with open(enc_path, "rb") as f:
                data = fer.decrypt(f.read())
        except InvalidToken:
            return None
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(name)[1] or ".bin")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        _media_cache[key] = {"path": tmp, "last": time.time(), "size": len(data)}
        return tmp


def drop_media_cache(vault_id, name):
    with _media_lock:
        entry = _media_cache.pop((vault_id, name), None)
    if entry:
        try:
            os.remove(entry["path"])
        except OSError:
            pass


def _evict_media_cache():
    removed = []
    with _media_lock:
        now = time.time()
        for k in list(_media_cache.keys()):
            if now - _media_cache[k]["last"] > MEDIA_TTL:
                removed.append(_media_cache.pop(k)["path"])
        total = sum(e["size"] for e in _media_cache.values())
        if total > MEDIA_MAX:
            for k, e in sorted(_media_cache.items(), key=lambda kv: kv[1]["last"]):
                if total <= MEDIA_MAX:
                    break
                total -= e["size"]
                removed.append(_media_cache.pop(k)["path"])
    for p in removed:
        try:
            os.remove(p)
        except OSError:
            pass


def purge_media_cache():
    with _media_lock:
        paths = [e["path"] for e in _media_cache.values()]
        _media_cache.clear()
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass


# ---------------- фоновые потоки ----------------
def _watchdog():
    while True:
        time.sleep(5)
        if (not IS_LOCKED and AUTOLOCK_MINUTES > 0 and
                time.time() - LAST_ACTIVITY > AUTOLOCK_MINUTES * 60):
            lock()


def _maintenance():
    while True:
        time.sleep(60)
        _evict_media_cache()


def start_background():
    threading.Thread(target=_watchdog, daemon=True).start()
    threading.Thread(target=_maintenance, daemon=True).start()