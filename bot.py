import asyncio
import os
import logging
import time
import threading

from telebot import TeleBot, types
from flask import Flask

# Безопасный импорт модулей
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

try:
    from database import DatabaseManager
    db = DatabaseManager()
    DB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database модуль недоступен: {e}")
    DB_AVAILABLE = False

# Инициализация бота (ПОСЛЕ импортов config)
bot = TeleBot(BOT_TOKEN)

# Веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 NFT Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)

# Запуск в отдельном потоке
web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояние для отслеживания ожидания адреса кошелька
waiting_for_wallet = {}

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
💎 TON: {'✅ Доступен' if TON_AVAILABLE else '⚠️ Загружается'}
🗃️ База данных: {'✅ Доступна' if DB_AVAILABLE else '❌ Недоступна'}

Основные команды:
/start - Начать работу
/help - Помощь  
/debug - Информация о системе
/connect - Подключить кошелек
/my_wallet - Мой кошелек

🚀 Версия: 1.0 (Render)
    """

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🟢 Статус')
    btn2 = types.KeyboardButton('ℹ️ Помощь')
    btn3 = types.KeyboardButton('💎 TON')
    btn4 = types.KeyboardButton('👛 Мой кошелек')
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    logger.info(f"👤 Пользователь {user.id} запустил бота")

@bot.message_handler(commands=['connect'])
def connect_wallet_command(message):
    """Подключение TON кошелька"""
    if not DB_AVAILABLE:
        bot.send_message(message.chat.id, "❌ База данных недоступна")
        return

    help_text = """
💎 Подключение TON кошелька:

Отправь мне адрес своего TON кошелька.

📱 Пример: EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c

Отправь свой TON адрес:
    """
    
    # Устанавливаем состояние ожидания адреса
    waiting_for_wallet[message.chat.id] = True
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['my_wallet'])
def my_wallet_command(message):
    """Показать информацию о кошельке"""
    if not DB_AVAILABLE:
        bot.send_message(message.chat.id, "❌ База данных недоступна")
        return

    wallet_address = db.get_wallet_address(message.from_user.id)
    
    if wallet_address:
        wallet_info = f"""
👛 Ваш TON кошелек:

📍 Адрес: `{wallet_address}`

💎 Для проверки баланса используйте:
/balance
        """
        bot.send_message(message.chat.id, wallet_info, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ У вас нет подключенного кошелька\nИспользуйте /connect чтобы подключить")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Команда помощи"""
    help_text = """
📋 Доступные команды:

/start - Начать работу
/help - Эта справка  
/debug - Техническая информация
/connect - Подключить кошелек TON
/my_wallet - Мой кошелек

🔧 Система работает на Render
💎 TON интеграция активна
🗃️ База данных доступна
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
💎 TON: {'✅ Доступен' if TON_AVAILABLE else '❌ Недоступен'}
🗃️ База данных: {'✅ Доступна' if DB_AVAILABLE else '❌ Недоступна'}

💡 Команды:
/connect - Подключить кошелек
/my_wallet - Мой кошелек
    """
    bot.send_message(message.chat.id, debug_text)

# Обработка ввода адреса кошелька
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех сообщений"""
    # Проверяем, ожидаем ли мы адрес кошелька
    if waiting_for_wallet.get(message.chat.id):
        handle_wallet_address(message)
    else:
        echo_message(message)

def handle_wallet_address(message):
    """Обработка адреса кошелька"""
    wallet_address = message.text.strip()
    
    # Проверяем формат TON адреса
    if wallet_address.startswith(('EQ', 'UQ', '0Q')) and len(wallet_address) >= 48:
        # Сохраняем в базу данных
        success = db.save_wallet_address(
            user_id=message.from_user.id,
            username=message.from_user.username or f"user_{message.from_user.id}",
            wallet_address=wallet_address
        )

        if success:
            bot.send_message(message.chat.id, f"✅ Кошелек подключен!\nАдрес: `{wallet_address}`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения кошелька. Возможно, адрес уже используется.")
    else:
        bot.send_message(message.chat.id, "❌ Неверный формат TON адреса\nПопробуйте снова или отправьте /cancel")
    
    # Сбрасываем состояние ожидания
    waiting_for_wallet[message.chat.id] = False

def echo_message(message):
    """Эхо-ответ для тестирования"""
    if message.text == '🟢 Статус':
        status_button(message)
    elif message.text == 'ℹ️ Помощь':
        help_button(message)
    elif message.text == '💎 TON':
        ton_button(message)
    elif message.text == '👛 Мой кошелек':
        my_wallet_command(message)
    else:
        bot.reply_to(message, f"🔍 Получено сообщение: {message.text}")

@bot.message_handler(func=lambda message: message.text == '🟢 Статус')
def status_button(message):
    """Кнопка статуса"""
    bot.send_message(message.chat.id, f"✅ Бот работает стабильно!\nХостинг: Render\nTON: {'✅' if TON_AVAILABLE else '⚠️'}\nБаза данных: {'✅' if DB_AVAILABLE else '❌'}")

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def help_button(message):
    """Кнопка помощи"""
    help_command(message)

@bot.message_handler(func=lambda message: message.text == '💎 TON')
def ton_button(message):
    """Кнопка TON"""
    if TON_AVAILABLE:
        ton_text = f"""
💎 TON Интеграция:

🌐 Сеть: {ton_manager.network}
✅ Статус: Активна
🔧 Функции: Баланс, кошельки, NFT
        """
    else:
        ton_text = "⚠️ TON интеграция временно недоступна"
    bot.send_message(message.chat.id, ton_text)

if __name__ == "__main__":
    logger.info("🤖 Запуск NFT бота для TON...")
    logger.info(f"💎 TON доступен: {TON_AVAILABLE}")
    logger.info(f"🗃️ База данных доступна: {DB_AVAILABLE}")

    # Инициализация TON провайдера (если доступен)
    if TON_AVAILABLE:
        try:
            asyncio.run(ton_manager.init_provider())
            logger.info("✅ TON провайдер инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации TON: {e}")
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

            if "409" in error_msg:
                logger.info("🕒 Обнаружен конфликт экземпляров, ждем 60 секунд...")
                time.sleep(60)
            else:
                logger.info("🔄 Перезапуск через 15 секунд...")
                time.sleep(15)
