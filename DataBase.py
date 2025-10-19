import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = 'nft_bot.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    wallet_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ База данных инициализирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            return False

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
            logger.info(f"✅ Кошелек сохранен для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения кошелька: {e}")
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
            logger.error(f"❌ Ошибка получения кошелька: {e}")
            return None

# Глобальный экземпляр базы данных
db = DatabaseManager()

def user_has_wallet(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя кошелек"""
    return get_wallet_address(user_id) is not None
