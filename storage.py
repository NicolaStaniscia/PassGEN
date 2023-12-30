import sqlite3 as sql
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Encode a string to bytes
def bytes_encoding(string):
    return string.encode("utf-8")

class Storage:

    def __init__(self):
        self.master_password = None
        self.name = None
        # Check if the storage exists
        if not os.path.exists("storage.db"):
            # Create the storage
            self.create_storage()
        else:
            self.conn = sql.connect("storage.db")
            self.cursor = self.conn.cursor()


    def create_storage(self):
        self.conn = sql.connect("storage.db")
        self.cursor = self.conn.cursor()
        # Create the tables
        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            salt TEXT NOT NULL,
                            username TEXT NOT NULL,
                            password TEXT NOT NULL
                        )''')
        self.conn.commit()
        self.conn.execute('''
                        CREATE TABLE IF NOT EXISTS storage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL REFERENCES users(id),
                            service TEXT NOT NULL,
                            username TEXT NOT NULL,
                            salt TEXT NOT NULL,
                            password TEXT NOT NULL
                        )
        ''')
        self.conn.commit()

    def check_user(self, name):
        # Get all the users
        self.cursor.execute('''
            SELECT id, salt, username FROM users
        ''')
        results = self.cursor.fetchall()
        # Check if the username exists
        for (id, salt, user) in results:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            salted_user = base64.b64encode(kdf.derive(bytes_encoding(name))).decode("utf-8")
            if salted_user == user:
                return id
        return None

    def user_registration(self, name, master_pass):
        # Check if the username already exists
        if self.check_user(name) is not None:
            return False
        self.name = bytes_encoding(name)
        self.master_password = bytes_encoding(master_pass)
        # Get the salt
        salt = os.urandom(16)
        # Create the key derivation function
        kdf = (PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        ), PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        ))
        # Get the salted username
        salted_user = base64.b64encode(kdf[0].derive(self.name)).decode("utf-8")
        # Get the salted hash
        salted_hash = base64.b64encode(kdf[1].derive(self.master_password)).decode("utf-8")
        # Insert the user into the database
        self.cursor.execute('''
            INSERT INTO users (salt, username, password) VALUES (?, ?, ?)
        ''', (salt, salted_user, salted_hash))
        self.conn.commit()
        return True

    def user_login(self, name, master_pass):
        # Check if the username exists
        if self.check_user(name) is None:
            return False
        user_id = self.check_user(name)
        name = name
        master_pass = bytes_encoding(master_pass)
        # Get the salt and the password
        self.cursor.execute('''
            SELECT salt, password FROM users WHERE id = ?
        ''', (user_id,))
        salt, password = self.cursor.fetchone()
        # Create the key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        # Get the salted hash for inserted password
        inserted_hash = base64.b64encode(kdf.derive(master_pass)).decode("utf-8")
        # Compare the hashes
        if inserted_hash == password:
            self.user_id = user_id
            self.name = name
            self.master_password = master_pass
            return True
        return False

    def delete_password(self, service):
        service = service.capitalize()
        self.cursor.execute('''
            SELECT id FROM storage WHERE service = ? AND user_id = ?''', (service, self.user_id))
        if self.cursor.fetchone() is None:
            return False
        # Delete the row
        self.cursor.execute('''
            DELETE FROM storage WHERE service = ? AND user_id = ?
        ''', (service, self.user_id))
        self.conn.commit()
        return True

    def add_password(self, service, username, password):
        service = service.capitalize()
        # Check if the service already exists
        self.cursor.execute('''
                        SELECT service FROM storage WHERE service = ? AND user_id = ?
                ''', (service, self.user_id))
        if self.cursor.fetchone() is not None:
            return False
        # Get the salt
        salt = os.urandom(16)
        # Create the key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        # Get the key
        key = base64.b64encode(kdf.derive(self.master_password))
        f = Fernet(key)
        # Encode the username and the password
        username = bytes_encoding(username)
        password = bytes_encoding(password)
        # Encrypt the username and the password
        encrypt_username = f.encrypt(username)
        encrypt_password = f.encrypt(password)
        # Insert information into the database
        self.cursor.execute('''
                INSERT INTO storage (user_id, service, username, salt, password) VALUES (?, ?, ?, ?, ?)
        ''', (self.user_id, service, encrypt_username, salt, encrypt_password))
        self.conn.commit()
        return True

    def update_password(self, service, old_password, new_password):
        service = service.capitalize()
        # Get the service id, the salt and the password
        self.cursor.execute('''
            SELECT id, salt, password FROM storage WHERE service = ? AND user_id = ?
        ''', (service, self.user_id))
        service_id, salt, password = self.cursor.fetchone()
        # Create the key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        # Get the key
        key = base64.b64encode(kdf.derive(self.master_password))
        f = Fernet(key)
        # Encode and decrypt the old password
        old_password = bytes_encoding(old_password)
        passwd = None
        try:
            passwd = f.decrypt(password)
        except:
            return False
        if old_password != passwd:
            return False
        # Encode and encrypt the new password
        new_password = bytes_encoding(new_password)
        encrypt_password = f.encrypt(new_password)
        # Update the password
        self.cursor.execute('''
            UPDATE storage SET password = ? WHERE id = ?
        ''', (encrypt_password, service_id))
        self.conn.commit()
        return True

    def show_services(self):
        self.cursor.execute('''
            SELECT id, service FROM storage WHERE user_id = ?
        ''', (self.user_id,))
        return self.cursor.fetchall()

    def retrieve_information(self, service):
        service = service.capitalize()
        # Retrieve the row
        self.cursor.execute('''
            SELECT username, salt, password FROM storage WHERE service = ? AND user_id = ?
        ''', (service, self.user_id))
        username, salt, password = self.cursor.fetchone()
        if username is not None and password is not None:
            # Create the key derivation function
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.b64encode(kdf.derive(self.master_password))
            f = Fernet(key)
            try:
                username = f.decrypt(username)
                password = f.decrypt(password)
                return username, password
            except:
                return None
        else:
            return None

    def close(self):
        self.conn.close()

