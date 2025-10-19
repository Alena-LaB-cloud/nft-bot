import sqlite3
import logging
from typing import Optional

import bot

logger = logging.getLogger(__name__)


@bot.message_handler(commands=['connect'])
def connect_wallet_command(message):
    """Подключение TON кошелька"""
    help_text = """
💎 Подключение TON кошелька:

Отправь мне адрес своего TON кошелька.

📱 Пример: EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c

Отправь свой TON адрес:
    """
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: True)
def handle_wallet_address(message):
    """Обработка адреса кошелька"""
    if message.text.startswith(('EQ', 'UQ', '0Q')) and len(message.text) >= 48:
        # Сохраняем в базу данных
        success = save_wallet_address(
            user_id=message.from_user.id,
            username=message.from_user.username or f"user_{message.from_user.id}",
            wallet_address=message.text
        )

        if success:
            bot.send_message(message.chat.id, f"✅ Кошелек подключен!\nАдрес: `{message.text}`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения кошелька")
    else:
        bot.send_message(message.chat.id, "❌ Неверный формат TON адреса")

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()

    # Таблица пользователей с кошельками
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            wallet_address TEXT UNIQUE,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица NFT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nfts (
            nft_id TEXT PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            description TEXT,
            image_path TEXT,
            price_ton REAL DEFAULT 0.0,
            for_sale BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")


def save_wallet_address(user_id: int, username: str, wallet_address: str) -> bool:
    """Сохраняет адрес кошелька в БД"""
    try:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, wallet_address)
            VALUES (?, ?, ?)
        ''', (user_id, username, wallet_address))

        conn.commit()
        conn.close()

        logger.info(f"✅ Wallet saved for user {user_id}: {wallet_address}")
        return True

    except sqlite3.IntegrityError:
        logger.error(f"❌ Wallet address already exists: {wallet_address}")
        return False
    except Exception as e:
        logger.error(f"❌ Error saving wallet: {e}")
        return False


def get_wallet_address(user_id: int) -> Optional[str]:
    """Получает адрес кошелька из БД"""
    try:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT wallet_address FROM users WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    except Exception as e:
        logger.error(f"❌ Error getting wallet: {e}")
        return None


def user_has_wallet(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя кошелек"""
    return get_wallet_address(user_id) is not None