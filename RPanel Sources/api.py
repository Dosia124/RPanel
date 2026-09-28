# api.py — HTTP API и страницы
import io
import os
import time
import random
import mimetypes
from functools import wraps
from threading import Timer

import requests
from flask import Flask, request, session, jsonify, redirect, send_file

import core
from ui_login import LOGIN_HTML
from ui_app import APP_HTML

app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def authed():
    return bool(session.get("authed")) and not core.IS_LOCKED and core.CURRENT_KEY


def require_auth(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not authed():
            return jsonify({"error": "locked"}), 403
        core.touch()
        return f(*a, **kw)
    return wrapper


@app.after_request
def _headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


def _login_page(first, error=""):
    return (LOGIN_HTML.replace("%%FIRST%%", "1" if first else "0")
            .replace("%%ERROR%%", error or ""))


@app.route("/")
def index():
    if authed():
        return APP_HTML
    return _login_page(not core.vault_exists())


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/login", methods=["POST"])
def login():
    first = not core.vault_exists()
    if core.login_blocked():
        return _login_page(first, "Too many failed attempts — wait a minute")
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")
    if first and password != confirm:
        return _login_page(True, "Passwords do not match")
    ok, err = core.unlock(password)
    if not ok:
        core.record_failure()
        return _login_page(first, err)
    core.clear_failures()
    session["authed"] = True
    session["current_vault"] = core.ensure_default_vault()[0]["id"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    core.lock()
    return redirect("/")


@app.route("/api/ping", methods=["POST"])
@require_auth
def ping():
    return jsonify({"ok": True})


@app.route("/api/settings", methods=["GET", "POST"])
@require_auth
def api_settings():
    if request.method == "POST":
        try:
            v = int((request.get_json(silent=True) or {}).get("autolock", 15))
        except (TypeError, ValueError):
            v = 15
        core.AUTOLOCK_MINUTES = max(0, min(240, v))
    return jsonify({"autolock": core.AUTOLOCK_MINUTES})


# ---------------- хранилища ----------------
@app.route("/api/vaults")
@require_auth
def api_vaults():
    return jsonify({"vaults": core.vaults_with_counts(),
                    "current": session.get("current_vault")})


@app.route("/api/vaults/create", methods=["POST"])
@require_auth
def api_vault_create():
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    vid = core.create_vault(name)
    session["current_vault"] = vid
    return jsonify({"success": True, "id": vid})


@app.route("/api/vaults/switch", methods=["POST"])
@require_auth
def api_vault_switch():
    vid = (request.get_json(silent=True) or {}).get("id")
    if any(v["id"] == vid for v in core.get_vaults()):
        session["current_vault"] = vid
        return jsonify({"success": True})
    return jsonify({"error": "Vault not found"}), 404


@app.route("/api/vaults/rename", methods=["POST"])
@require_auth
def api_vault_rename():
    data = request.get_json(silent=True) or {}
    if core.rename_vault(data.get("id"), data.get("name", "")):
        return jsonify({"success": True})
    return jsonify({"error": "Vault not found"}), 404


@app.route("/api/vaults/delete", methods=["POST"])
@require_auth
def api_vault_delete():
    vid = (request.get_json(silent=True) or {}).get("id")
    new_current = core.delete_vault(vid)
    if new_current is False:
        return jsonify({"error": "Vault not found"}), 404
    session["current_vault"] = new_current
    return jsonify({"success": True, "current": new_current})


# ---------------- файлы ----------------
@app.route("/api/files")
@require_auth
def api_files():
    vid = session.get("current_vault")
    if not vid:
        return jsonify({"error": "no vault"}), 400
    trash = request.args.get("trash") == "1"
    return jsonify({
        "files": core.list_files(vid, trash=trash),
        "all_names": core.list_vault_names(vid),
        "stats": core.get_stats(vid),
        "inbox_count": len(core.list_inbox()),
        "vaults": core.vaults_with_counts(),
        "current": vid,
    })


@app.route("/api/upload", methods=["POST"])
@require_auth
def api_upload():
    vid = session.get("current_vault")
    added, dups = 0, []
    for file in request.files.getlist("files[]"):
        name = core.sanitize_filename(file.filename or "")
        if os.path.splitext(name)[1].lower() not in core.MEDIA_EXTS:
            continue
        data = file.read()
        if not data:
            continue
        res = core.add_media(vid, name, data)
        if res["status"] == "ok":
            added += 1
        elif res["status"] == "duplicate":
            dups.append(res["name"])
    return jsonify({"success": True, "added": added, "duplicates": dups})


@app.route("/api/import", methods=["POST"])
@require_auth
def api_import():
    added, dups = core.import_inbox(session.get("current_vault"))
    return jsonify({"success": True, "added": added, "duplicates": dups})


@app.route("/api/export")
@require_auth
def api_export():
    vid = session.get("current_vault")
    name = request.args.get("filename", "")
    if not core.valid_name(name):
        return "Bad request", 400
    for path in (core.vault_path(vid, name + ".enc"),
                 core.vault_path(vid, "trash", name + ".enc")):
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = core.fernet().decrypt(f.read())
            return send_file(io.BytesIO(data), as_attachment=True, download_name=name)
    return "Not found", 404


@app.route("/api/meta", methods=["POST"])
@require_auth
def api_meta():
    data = request.get_json(silent=True) or {}
    name = data.get("filename", "")
    if not core.valid_name(name):
        return jsonify({"error": "bad name"}), 400
    core.update_meta(session.get("current_vault"), name,
                     tags=data.get("tags"), fav=data.get("fav"))
    return jsonify({"success": True})


@app.route("/api/bulk", methods=["POST"])
@require_auth
def api_bulk():
    vid = session.get("current_vault")
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action == "empty":
        n = 0
        for name in core.list_trash_names(vid):
            core.purge_file(vid, name)
            n += 1
        return jsonify({"success": True, "affected": n})
    names = [n for n in data.get("files", [])
             if isinstance(n, str) and core.valid_name(n)]
    if not names:
        return jsonify({"error": "no files"}), 400
    if action in ("tag_add", "tag_remove"):
        tags = [t.strip() for t in data.get("tags", [])
                if isinstance(t, str) and t.strip()]
        core.bulk_update(vid, names,
                         add_tags=tags if action == "tag_add" else None,
                         remove_tags=tags if action == "tag_remove" else None)
    elif action == "fav":
        core.bulk_update(vid, names, fav=True)
    elif action == "delete":
        for n in names:
            core.trash_file(vid, n)
    elif action == "restore":
        for n in names:
            core.restore_file(vid, n)
    elif action == "purge":
        for n in names:
            core.purge_file(vid, n)
    else:
        return jsonify({"error": "bad action"}), 400
    return jsonify({"success": True, "affected": len(names)})


@app.route("/api/change_password", methods=["POST"])
@require_auth
def api_change_password():
    data = request.get_json(silent=True) or {}
    ok, msg = core.change_password(data.get("old_pass") or "",
                                   data.get("new_pass") or "")
    if ok:
        return jsonify({"success": True, "message": msg})
    return jsonify({"error": msg}), 400


@app.route("/api/shutdown", methods=["POST"])
@require_auth
def api_shutdown():
    def _quit():
        core.purge_media_cache()
        os._exit(0)
    Timer(0.7, _quit).start()
    return jsonify({"success": True})


# ---------------- медиа ----------------
@app.route("/thumbnail/<path:filename>")
@require_auth
def thumbnail(filename):
    vid = session.get("current_vault")
    if not vid or not core.valid_name(filename):
        return "", 400
    data = core.get_thumbnail(vid, filename)
    if data is None:
        return "", 404
    mime = "image/gif" if data[:3] == b"GIF" else "image/jpeg"
    resp = app.response_class(data, mimetype=mime)
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp


@app.route("/media/<path:filename>")
@require_auth
def media(filename):
    vid = session.get("current_vault")
    if not vid or not core.valid_name(filename):
        return "", 400
    tmp = core.get_media_temp(vid, filename)
    if not tmp:
        return "Not found", 404
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    resp = send_file(tmp, mimetype=mime, conditional=True)
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp


# ---------------- rule34 ----------------
@app.route("/api/r34_config", methods=["GET", "POST"])
@require_auth
def api_r34_config():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        core.save_r34_config(data.get("api_key", ""), data.get("user_id", ""))
        return jsonify({"success": True})
    return jsonify(core.load_r34_config())


@app.route("/api/r34_tags")
@require_auth
def api_r34_tags():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])
    try:
        r = requests.get("https://rule34.xxx/autocomplete.php",
                         params={"q": q, "limit": "12"}, headers=UA, timeout=6)
        data = r.json()
    except Exception:
        return jsonify([])
    out = []
    for item in data if isinstance(data, list) else []:
        t = (item.get("value") or item.get("label") or "") if isinstance(item, dict) else str(item)
        if t:
            out.append(t)
    return jsonify(out[:12])


def _r34_fetch(tags, pid):
    cfg = core.load_r34_config()
    params = {"page": "dapi", "s": "post", "q": "index", "json": "1",
              "limit": 100, "pid": pid, "tags": tags}
    if cfg.get("api_key"):
        params["api_key"] = cfg["api_key"]
    if cfg.get("user_id"):
        params["user_id"] = cfg["user_id"]
    r = requests.get("https://api.rule34.xxx/index.php", params=params,
                     headers=UA, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    posts = []
    for p in data:
        url = p.get("file_url") or p.get("sample_url") or p.get("preview_url")
        if not url:
            continue
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith("http"):
            url = "https://rule34.xxx/" + url.lstrip("/")
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        mtype = core.MEDIA_EXTS.get(ext)
        if not mtype:
            continue
        ptags = p.get("tags", [])
        if isinstance(ptags, str):
            ptags = ptags.split()
        posts.append({"id": p.get("id"), "url": url, "type": mtype, "tags": ptags})
    return posts


@app.route("/api/r34_search", methods=["POST"])
@require_auth
def api_r34_search():
    tags = (request.get_json(silent=True) or {}).get("tags", "")
    if isinstance(tags, list):
        tags = " ".join(str(t) for t in tags)
    tags = str(tags).strip()
    try:
        posts = _r34_fetch(tags, random.randint(0, 8))
        if not posts:
            posts = _r34_fetch(tags, 0)
        if not posts:
            return jsonify({"error": "Nothing found for these tags"}), 404
        random.shuffle(posts)
        return jsonify({"posts": posts[:40]})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Rule34 request failed: %s" % e}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/r34_save", methods=["POST"])
@require_auth
def api_r34_save():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    tags = data.get("tags", [])
    post_id = data.get("id")
    if not url or not isinstance(tags, list):
        return jsonify({"error": "bad request"}), 400

    raw = data.get("vault")
    targets = raw if isinstance(raw, list) else ([raw] if raw else [])
    valid = {v["id"] for v in core.get_vaults()}
    targets = [t for t in targets if t in valid] or [session.get("current_vault")]

    ext = os.path.splitext(url.split("?")[0])[1].lower()
    if ext not in core.MEDIA_EXTS:
        return jsonify({"error": "unsupported media type"}), 400
    try:
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        content = r.content
    except Exception as e:
        return jsonify({"error": "Download failed: %s" % e}), 500

    name = "r34_%s%s" % (post_id if post_id else int(time.time()), ext)
    saved, dups, errors = [], [], []
    for vid in targets:
        res = core.add_media(vid, name, content, tags=tags)
        if res["status"] == "ok":
            saved.append({"vault": vid, "name": res["name"]})
        elif res["status"] == "duplicate":
            dups.append({"vault": vid, "name": res["name"]})
        else:
            errors.append(vid)
    return jsonify({
        "success": bool(saved),
        "saved": saved,
        "duplicates": dups,
        "errors": errors,
        "duplicate": bool(dups) and not saved,
        "name": (saved or dups or [{}])[0].get("name"),
    })


@app.route("/api/export_vault")
@require_auth
def api_export_vault():
    vid = session.get("current_vault")
    if not vid:
        return jsonify({"error": "no vault"}), 400
    vname = next((v["name"] for v in core.get_vaults() if v["id"] == vid), "vault")
    zpath = core.export_vault_zip(vid, include_trash=request.args.get("trash") == "1")
    if not zpath:
        return jsonify({"error": "Export failed"}), 500

    def _rm():
        try:
            os.remove(zpath)
        except OSError:
            pass

    Timer(600, _rm).start()
    resp = send_file(zpath, as_attachment=True, mimetype="application/zip",
                     download_name=core.sanitize_filename(vname) + ".zip")
    resp.headers["Cache-Control"] = "no-store"
    return resp
