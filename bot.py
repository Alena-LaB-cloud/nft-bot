import asyncio
import os
import logging
import time
import threading

from telebot import TeleBot, types
from flask import Flask

import ton_manager
from config import ADMIN_IDS, MIN_NFT_PRICE, MAX_NFT_PRICE

# Веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 NFT Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy"

@app.route('/ping')
def ping():
    return "pong"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)

# Запуск веб-сервера в отдельном потоке
web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
# Инициализация бота (ПОСЛЕ импортов config)
bot = TeleBot("8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc")

# Команды бота (остаются без изменений)
@bot.message_handler(commands=['start'])
def start_command(message):
    """Команда /start"""
    user = message.from_user

    welcome_text = f"""
🎨 Привет, {user.first_name}!

Я бот для создания NFT в сети TON!

✨ Бот успешно запущен на Render!
✅ Все системы работают

Основные команды:
/start - Начать работу
/help - Помощь
/debug - Информация о системе

🚀 Версия: 1.0 (Render)
    """

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🟢 Статус')
    btn2 = types.KeyboardButton('ℹ️ Помощь')
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    logger.info(f"👤 Пользователь {user.id} запустил бота")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Команда помощи"""
    help_text = """
📋 Доступные команды:

/start - Начать работу
/help - Эта справка  
/debug - Техническая информация

🔧 Система работает на Render
💎 TON интеграция готовится
🎨 NFT функционал в разработке
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['debug'])
def debug_command(message):
    """Отладочная информация"""
    debug_text = f"""
🔧 Системная информация:

🤖 Бот: Активен ✅
🌐 Хостинг: Render
🔑 Токен: {'✅ Установлен' if BOT_TOKEN else '❌ Отсутствует'}
📊 Логи: Включены

💡 Следующие шаги:
1. Проверить подключение к TON
2. Добавить базу данных
3. Включить NFT функционал
    """
    bot.send_message(message.chat.id, debug_text)
    logger.info(f"🔧 Отладочная информация запрошена пользователем {message.from_user.id}")

@bot.message_handler(func=lambda message: message.text == '🟢 Статус')
def status_button(message):
    """Кнопка статуса"""
    bot.send_message(message.chat.id, "✅ Бот работает стабильно!\nХостинг: Render\nСтатус: Online")

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def help_button(message):
    """Кнопка помощи"""
    help_command(message)

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    """Эхо-ответ для тестирования"""
    bot.reply_to(message, f"🔍 Получено сообщение: {message.text}")

if __name__ == "__main__":
    logger.info("🤖 Запуск NFT бота для TON...")
    logger.info(f"👑 Администраторы: {ADMIN_IDS}")
    logger.info(f"💎 Сеть TON: {ton_manager.network}")
    logger.info(f"💰 Диапазон цен: {MIN_NFT_PRICE}-{MAX_NFT_PRICE} TON")

    # Даем время запуститься веб-серверу
    time.sleep(3)
    logger.info("🌐 Веб-сервер запущен в отдельном потоке")

    # Инициализация TON провайдера
   try:
    import ton_manager
    from config import BOT_TOKEN, ADMIN_IDS, MIN_NFT_PRICE, MAX_NFT_PRICE, TON_NETWORK
    TON_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Config модули недоступны: {e}")
    # Значения по умолчанию
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
    ADMIN_IDS = [788630583]  # ваш ID из config.py
    MIN_NFT_PRICE = 0.1
    MAX_NFT_PRICE = 10.0
    TON_NETWORK = 'testnet'
    TON_AVAILABLE = False

    # Бесконечный цикл с перезапуском при ошибках для Render
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

            # Если ошибка 409 (конфликт экземпляров), ждем дольше
            if "409" in error_msg:
                logger.info("🕒 Обнаружен конфликт экземпляров, ждем 60 секунд...")
                time.sleep(60)
            else:
                logger.info("🔄 Перезапуск через 15 секунд...")
                time.sleep(15)




