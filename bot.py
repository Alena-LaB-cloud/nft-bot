import asyncio
import os
import logging
import time
import threading
import random
from datetime import datetime

from telebot import TeleBot, types

print("🟢 DEBUG: Starting bot imports...")

# ========== КОНФИГУРАЦИЯ ==========
try:
    from config import BOT_TOKEN, ADMIN_IDS, MIN_NFT_PRICE, MAX_NFT_PRICE, TON_NETWORK
    print("✅ DEBUG: Config imported successfully")
except ImportError as e:
    print(f"❌ DEBUG: Config import failed: {e}")
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
    ADMIN_IDS = [788630583]
    MIN_NFT_PRICE = 0.1
    MAX_NFT_PRICE = 10.0
    TON_NETWORK = 'testnet'

# ========== БАЗА ДАННЫХ ==========
try:
    from database import DatabaseManager
    db = DatabaseManager()
    DB_AVAILABLE = True
    print("✅ DEBUG: Database imported and initialized")
except ImportError as e:
    print(f"❌ DEBUG: Database import failed: {e}")
    DB_AVAILABLE = False
except Exception as e:
    print(f"❌ DEBUG: Database initialization failed: {e}")
    DB_AVAILABLE = False

# ========== СИМУЛЯТОР ТРАНЗАКЦИЙ ==========
TX_SIMULATOR_AVAILABLE = False  # Временно отключим

print("🟢 DEBUG: All imports completed")

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = TeleBot(BOT_TOKEN)
print("✅ DEBUG: Bot initialized")

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
print("✅ DEBUG: Logging configured")

# ========== СОСТОЯНИЯ ==========
waiting_for_wallet = {}
waiting_for_nft = {}
waiting_for_sale = {}
waiting_for_gift = {}

# ========== ХРАНИЛИЩЕ NFT ==========
user_nfts = {}

print("🟢 DEBUG: Bot initialization complete!")
print(f"🔧 DEBUG: DB_AVAILABLE = {DB_AVAILABLE}")
print(f"🔧 DEBUG: TX_SIMULATOR_AVAILABLE = {TX_SIMULATOR_AVAILABLE}")

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    """Команда /start"""
    user = message.from_user

    welcome_text = f"""
🎨 Привет, {user.first_name}!

Я бот для создания и торговли NFT в сети TON!

✨ Создавай, продавай и дари NFT!
✅ Все системы работают

Основные команды:
/start - Начать работу
/help - Помощь  
/nft - Создать NFT
/my_nfts - Мои NFT
/market - Маркетплейс

🚀 Версия: 2.0 (NFT Marketplace)
    """

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = types.KeyboardButton('🟢 Статус')
    btn2 = types.KeyboardButton('ℹ️ Помощь')
    btn3 = types.KeyboardButton('💎 TON')
    btn4 = types.KeyboardButton('👛 Мой кошелек')
    btn5 = types.KeyboardButton('🎨 Создать NFT')
    btn6 = types.KeyboardButton('🖼️ Мои NFT')
    btn7 = types.KeyboardButton('💰 Продать NFT')
    btn8 = types.KeyboardButton('🎁 Подарить NFT')
    btn9 = types.KeyboardButton('🏪 Маркетплейс')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    logger.info(f"👤 Пользователь {user.id} запустил бота")

# ... остальной код команд (оставьте без изменений) ...

if __name__ == "__main__":
    logger.info("🤖 Запуск NFT бота с маркетплейсом...")
    logger.info(f"🗃️ База данных доступна: {DB_AVAILABLE}")

    while True:
        try:
            logger.info("🔄 Запуск polling бота...")
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Ошибка при работе бота: {error_msg}")
            logger.info("🔄 Перезапуск через 15 секунд...")
            time.sleep(15)


