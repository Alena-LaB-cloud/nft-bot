import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

print("🟢 DEBUG: database.py is loading")

class DatabaseManager:
    def __init__(self, db_path: str = 'bot_database.db'):
        print(f"🟢 DEBUG: DatabaseManager __init__ called")
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        try:
            print(f"🟢 DEBUG: Initializing database at {self.db_path}")
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    wallet_address TEXT UNIQUE
                )
            ''')

            conn.commit()
            conn.close()
            print("✅ DEBUG: Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ DEBUG: Database init error: {e}")
            return False

    def save_wallet_address(self, user_id: int, username: str, wallet_address: str) -> bool:
        """Сохраняет адрес кошелька в БД"""
        try:
            print(f"🟢 DEBUG: Saving wallet for user {user_id}")
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, wallet_address)
                VALUES (?, ?, ?)
            ''', (user_id, username, wallet_address))

            conn.commit()
            conn.close()
            print("✅ DEBUG: Wallet saved successfully")
            return True
        except Exception as e:
            print(f"❌ DEBUG: Save wallet error: {e}")
            return False

    def get_wallet_address(self, user_id: int):
        """Получает адрес кошелька из БД"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            cursor.execute('SELECT wallet_address FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else None
        except Exception as e:
            print(f"❌ DEBUG: Get wallet error: {e}")
            return None

def user_has_wallet(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя кошелек"""
    return get_wallet_address(user_id) is not None
