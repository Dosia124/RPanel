import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Конфигурация (должна совпадать с основным скриптом)
VAULT_FOLDER = "vault"
SALT_FILE = "salt.bin"
MASTER_KEY_FILE = "master.key.enc"
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

def main():
    print("--- УТИЛИТА РАСШИФРОВКИ ХРАНИЛИЩА ---")
    password = input("Введите пароль от хранилища: ")
    
    try:
        master_key = get_master_key(password)
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        return

    if not master_key:
        print("Ошибка: Неверный пароль!")
        return

    if not os.path.exists(VAULT_FOLDER):
        print(f"Ошибка: Папка '{VAULT_FOLDER}' не найдена!")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    fernet = Fernet(master_key)
    decrypted_count = 0
    failed_count = 0

    print(f"\nНачинаем расшифровку файлов из папки '{VAULT_FOLDER}'...")

    for filename in os.listdir(VAULT_FOLDER):
        if filename.endswith('.enc'):
            enc_filepath = os.path.join(VAULT_FOLDER, filename)
            original_name = filename[:-4] # Убираем '.enc'
            
            try:
                with open(enc_filepath, 'rb') as f:
                    enc_data = f.read()
                
                dec_data = fernet.decrypt(enc_data)
                
                out_filepath = os.path.join(OUTPUT_FOLDER, original_name)
                
                # Если файл с таким именем уже существует, добавляем цифру
                base, ext = os.path.splitext(original_name)
                counter = 1
                while os.path.exists(out_filepath):
                    out_filepath = os.path.join(OUTPUT_FOLDER, f"{base}_{counter}{ext}")
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
    print(f"Ваши файлы находятся в папке '{OUTPUT_FOLDER}'.")
    print("Теперь вы можете скопировать их в папку 'inbox' новой версии хранилища.")

if __name__ == "__main__":
    main()
