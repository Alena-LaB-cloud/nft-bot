import os
import asyncio
import logging
import time
import threading
from telebot import TeleBot, types
from flask import Flask

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Веб-сервер для Render
app = Flask(__name__)


@app.route('/')
def home():
    return "🤖 NFT Bot is running!"


def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)


# Запуск веб-сервера в отдельном потоке
web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

# Инициализация бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
bot = TeleBot(BOT_TOKEN)


# Команды бота
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
    """
    bot.send_message(message.chat.id, debug_text)


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
    logger.info("🚀 Запуск NFT бота на Render...")

    try:
        bot.infinity_polling()
        logger.info("🤖 Бот успешно запущен!")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")