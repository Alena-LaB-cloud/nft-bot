import sqlite3
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = 'bot_database.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
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
        logger.info("✅ Database initialized")

    def save_wallet_address(self, user_id: int, username: str, wallet_address: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, wallet_address)
                VALUES (?, ?, ?)
            ''', (user_id, username, wallet_address))
            conn.commit()
            conn.close()
            logger.info(f"✅ Wallet saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving wallet: {e}")
            return False

    def get_wallet_address(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Error getting wallet: {e}")
            return None

def user_has_wallet(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя кошелек"""
    return get_wallet_address(user_id) is not None
