import os
import base64
import json
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Конфигурация (должна совпадать с основным скриптом)
VAULTS_DIR = "vaults"
SALT_FILE = "salt.bin"
MASTER_KEY_FILE = "master.key.enc"
VAULT_REGISTRY_FILE = "vaults.enc"
OUTPUT_FOLDER = "decrypted_files"

def get_salt():
    if not os.path.exists(SALT_FILE):
        raise FileNotFoundError(f"Файл '{SALT_FILE}' не найден! Поместите скрипт в папку с вашим хранилищем.")
    with open(SALT_FILE, 'rb') as f: 
        return f.read()

def derive_key(password):
    salt = get_salt()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def get_master_key(password):
    if not os.path.exists(MASTER_KEY_FILE):
        raise FileNotFoundError(f"Файл '{MASTER_KEY_FILE}' не найден!")
    with open(MASTER_KEY_FILE, 'rb') as f: 
        enc_master = f.read()
    try:
        return Fernet(derive_key(password)).decrypt(enc_master)
    except InvalidToken:
        return None

def get_vaults(master_key):
    if not os.path.exists(VAULT_REGISTRY_FILE):
        raise FileNotFoundError(f"Файл '{VAULT_REGISTRY_FILE}' не найден!")
    with open(VAULT_REGISTRY_FILE, 'rb') as f: 
        enc_data = f.read()
    try:
        dec_data = Fernet(master_key).decrypt(enc_data)
        return json.loads(dec_data)
    except InvalidToken:
        return None

def sanitize_foldername(name):
    # Убираем недопустимые символы из имени папки для ОС
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

def main():
    print("--- УТИЛИТА РАСШИФРОВКИ ХРАНИЛИЩА ---")
    password = input("Введите мастер-пароль: ")
    
    try:
        master_key = get_master_key(password)
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        return

    if not master_key:
        print("Ошибка: Неверный пароль!")
        return

    try:
        vaults = get_vaults(master_key)
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        return

    if not vaults:
        print("Ошибка: Не найдено ни одного хранилища!")
        return

    print("\nДоступные хранилища:")
    for i, vault in enumerate(vaults):
        print(f"  [{i}] {vault['name']} (Папка: {vault['id']})")
    
    try:
        selection = input("\nВведите номер хранилища для расшифровки: ")
        selection_idx = int(selection)
        if selection_idx < 0 or selection_idx >= len(vaults):
            print("Ошибка: Неверный номер.")
            return
    except ValueError:
        print("Ошибка: Нужно ввести число.")
        return

    selected_vault = vaults[selection_idx]
    vault_id = selected_vault['id']
    vault_name = selected_vault['name']

    vault_path = os.path.join(VAULTS_DIR, vault_id)
    if not os.path.exists(vault_path):
        print(f"Ошибка: Папка хранилища '{vault_path}' не найдена на диске!")
        return

    # Создаем папку вывода с понятным именем
    safe_name = sanitize_foldername(vault_name)
    out_dir = os.path.join(OUTPUT_FOLDER, safe_name)
    os.makedirs(out_dir, exist_ok=True)
    
    fernet = Fernet(master_key)
    decrypted_count = 0
    failed_count = 0

    print(f"\nНачинаем расшифровку файлов из хранилища '{vault_name}'...")

    for filename in os.listdir(vault_path):
        # Расшифровываем только медиа файлы, игнорируем tags.enc
        if filename.endswith('.enc') and filename != 'tags.enc':
            enc_filepath = os.path.join(vault_path, filename)
            original_name = filename[:-4] # Убираем '.enc'
            
            try:
                with open(enc_filepath, 'rb') as f:
                    enc_data = f.read()
                
                dec_data = fernet.decrypt(enc_data)
                
                out_filepath = os.path.join(out_dir, original_name)
                
                # Если файл с таким именем уже существует, добавляем цифру
                base, ext = os.path.splitext(original_name)
                counter = 1
                while os.path.exists(out_filepath):
                    out_filepath = os.path.join(out_dir, f"{base}_{counter}{ext}")
                    counter += 1
                    
                with open(out_filepath, 'wb') as f:
                    f.write(dec_data)
                    
                decrypted_count += 1
                print(f"  [OK] {original_name}")
            except InvalidToken:
                print(f"  [FAIL] {filename} (Файл поврежден или ключ не совпадает)")
                failed_count += 1
            except Exception as e:
                print(f"  [ERROR] {filename}: {e}")
                failed_count += 1

    print("\n" + "="*40)
    print(f"Готово! Успешно расшифровано: {decrypted_count}")
    if failed_count > 0:
        print(f"Ошибок: {failed_count}")
    print(f"Ваши файлы находятся в папке: '{out_dir}'")
    print("Теперь вы можете перенести их в папку 'inbox' новой версии Media Vault.")

if __name__ == "__main__":
    main()