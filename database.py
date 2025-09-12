import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print("Успешное подключение к MySQL")
        except Error as e:
            print(f"Ошибка подключения к MySQL: {e}")
    
    def create_tables(self):
        cursor = self.connection.cursor()
        try:
            # Создание таблиц
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    hashpass VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS banner (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT NOT NULL,
                    author BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    send_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (author) REFERENCES user(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bound (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    banner_id INT NOT NULL,
                    receiver BIGINT NOT NULL,
                    FOREIGN KEY (banner_id) REFERENCES banner(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.commit()
            print("Таблицы успешно созданы")
        except Error as e:
            print(f"Ошибка создания таблиц: {e}")
        finally:
            cursor.close()
    
    def user_exists(self, user_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT id FROM user WHERE id = %s", (user_id,))
            return cursor.fetchone() is not None
        except Error as e:
            print(f"Ошибка проверки существования пользователя: {e}")
            return False
        finally:
            cursor.close()
    
    def create_user(self, user_id, username, first_name, password):
        cursor = self.connection.cursor()
        try:
            hashpass = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO user (id, username, first_name, hashpass) 
                VALUES (%s, %s, %s, %s)
            """, (user_id, username, first_name, hashpass))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка создания пользователя: {e}")
            return False
        finally:
            cursor.close()
    
    def check_password(self, user_id, password):
        cursor = self.connection.cursor()
        try:
            hashpass = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("SELECT id FROM user WHERE id = %s AND hashpass = %s", 
                          (user_id, hashpass))
            return cursor.fetchone() is not None
        except Error as e:
            print(f"Ошибка проверки пароля: {e}")
            return False
        finally:
            cursor.close()
    
    def change_password(self, user_id, new_password):
        cursor = self.connection.cursor()
        try:
            hashpass = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE user SET hashpass = %s WHERE id = %s", 
                          (hashpass, user_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Ошибка смены пароля: {e}")
            return False
        finally:
            cursor.close()
    
    def create_banner(self, author_id, message, send_at):
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO banner (author, message, send_at, is_active) 
                VALUES (%s, %s, %s, %s)
            """, (author_id, message, send_at, True))
            banner_id = cursor.lastrowid
            self.connection.commit()
            return banner_id
        except Error as e:
            print(f"Ошибка создания баннера: {e}")
            return None
        finally:
            cursor.close()
    
    def add_receiver(self, banner_id, receiver_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO bound (banner_id, receiver) 
                VALUES (%s, %s)
            """, (banner_id, receiver_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка добавления получателя: {e}")
            return False
        finally:
            cursor.close()
    
    def get_user_banners(self, user_id):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM banner 
                WHERE author = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка получения баннеров: {e}")
            return []
        finally:
            cursor.close()
    
    def get_banner_by_id(self, banner_id):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM banner WHERE id = %s", (banner_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Ошибка получения баннера: {e}")
            return None
        finally:
            cursor.close()
    
    def update_banner_message(self, banner_id, message):
        cursor = self.connection.cursor()
        try:
            cursor.execute("UPDATE banner SET message = %s WHERE id = %s", 
                          (message, banner_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Ошибка обновления сообщения: {e}")
            return False
        finally:
            cursor.close()
    
    def update_banner_send_at(self, banner_id, send_at):
        cursor = self.connection.cursor()
        try:
            cursor.execute("UPDATE banner SET send_at = %s WHERE id = %s", 
                          (send_at, banner_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Ошибка обновления времени отправки: {e}")
            return False
        finally:
            cursor.close()
    
    def toggle_banner_active(self, banner_id, is_active):
        cursor = self.connection.cursor()
        try:
            cursor.execute("UPDATE banner SET is_active = %s WHERE id = %s", 
                          (is_active, banner_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Ошибка изменения статуса баннера: {e}")
            return False
        finally:
            cursor.close()
    
    def get_banner_receivers(self, banner_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT receiver FROM bound WHERE banner_id = %s", (banner_id,))
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            print(f"Ошибка получения получателей: {e}")
            return []
        finally:
            cursor.close()
    
    def delete_banner_receivers(self, banner_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM bound WHERE banner_id = %s", (banner_id,))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка удаления получателей: {e}")
            return False
        finally:
            cursor.close()
    
    def delete_banner(self, banner_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM banner WHERE id = %s", (banner_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Ошибка удаления баннера: {e}")
            return False
        finally:
            cursor.close()
    
    def get_banners_to_send(self):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT b.*, u.username as author_username, u.first_name as author_name
                FROM banner b
                JOIN user u ON b.author = u.id
                WHERE b.is_active = TRUE AND b.send_at <= NOW()
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка получения баннеров для отправки: {e}")
            return []
        finally:
            cursor.close()
    
    def get_banner_receivers_with_data(self, banner_id):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT b.receiver, u.username, u.first_name
                FROM bound b
                JOIN user u ON b.receiver = u.id
                WHERE b.banner_id = %s
            """, (banner_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка получения получателей с данными: {e}")
            return []
        finally:
            cursor.close()
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()