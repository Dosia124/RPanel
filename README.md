# 🔐 RPanel - Media Vault

**RPanel** is a local, highly secure media vault (images, GIFs, videos) with "zero-knowledge" encryption. All your files are encrypted on disk using Fernet (AES) symmetric encryption and are accessible only through a convenient local web interface.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask)

---

## ✨ Key Features

- 🔒 **On-the-fly Encryption:** The master key is encrypted using a password (PBKDF2HMAC-SHA256). Files on disk are stored as unreadable `.enc` blocks.
- 🏷️ **Tagging System:** Assign tags to any media file. Tags are highlighted directly in the viewer and are clickable—clicking a tag instantly filters the gallery.
- 🔍 **Smart Search:** Typing tags brings up a dropdown with autocomplete (up to 5 suggestions), showing how many files are associated with each tag. You can navigate the list using keyboard arrow keys.
- 🎞️ **Universal Viewer:** Supports images, animated GIFs, and videos (mp4, webm, mkv) with on-the-fly thumbnail generation.
- 🌐 **Local Web UI:** Modern Apple-style interface (supports light and dark themes) without the need for databases. All settings are cached in the browser.
- ⚡ **Auto-Shutdown (Heartbeat):** If you close the tab or browser, the app detects it and automatically shuts down the server after 15 seconds. There is also a manual shutdown button.
- 🖥️ **Standalone `.exe`:** Can be compiled into a single executable file without a black console window or unnecessary dependencies.

---

## ⌨️ Keyboard Shortcuts (in Viewer Mode)

| Key | Action |
| :--- | :--- |
| `A` / `D` | Previous / Next media |
| `W` / `A` / `S` / `D` | Pan (move) — *only when zoom > 100%* |
| `Z` / `X` | Zoom In / Out |
| `C` | Reset zoom and position |
| `T` | Open tag editing panel |
| `Space` | Pause / Play (for videos) |
| `H` | Hide/Show UI (focus mode) |
| `Del` | Delete current file |
| `Esc` | Close viewer |

---

## 🛠️ Installation & Running (From Source)

1. Make sure you have Python 3.8+ installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/Dosia124/RPanel.git
   cd RPanel
   ```
3. Install dependencies:
   ```bash
   pip install flask cryptography pillow opencv-python-headless
   ```
   *(Optional: `opencv-python-headless` is required for video thumbnail generation)*
4. Run the application:
   ```bash
   python media_vault.py
   ```
5. Your browser will open automatically. On first launch, enter a password—this will become your master password for the vault.

---

## 📦 Building the `.exe` (Windows)

To create a standalone file with UPX compression and a hidden console, use `PyInstaller`. 
Ensure that `icon.ico` and `upx.exe` are in the project folder (if you want compression).

Run the following command:

```bash
py -m PyInstaller --onefile --windowed --upx-dir . --exclude-module tkinter --exclude-module matplotlib --exclude-module scipy --exclude-module pandas --name RPanel --icon icon.ico media_vault.py
```

The compiled `RPanel.exe` will appear in the `dist/` folder.

---

## 📂 Project Structure

- `media_vault.py` — main script (server, encryption logic, and Web UI).
- `salt.bin` — auto-generated cryptographic salt.
- `master.key.enc` — encrypted master key.
- `tags.json` — local tag database.
- `inbox/` — quick import folder (drop files here and click the Import button).
- `vault/` — encrypted storage (do not manually delete files inside!).

---

## ⚠️ Important!

**Do not lose your password!** Without the password, decrypting `master.key.enc` is impossible. All cryptography is built on the standards of the `cryptography` library; there are no backdoors.

If you need to transfer the vault to a new PC or rebuild the program, simply copy the `vault/` folder along with the `salt.bin`, `master.key.enc`, and `tags.json` files.

---

## 🤝 Open Source Contribution

This is an open-source project! Anyone is welcome to modify the code, add their own features, or submit pull requests. Feel free to fork the repository and make it your own. If you encounter any bugs or have ideas for new features, please open an issue!
