import asyncio
import os
import logging
import time
import threading
import random
from datetime import datetime

from telebot import TeleBot, types
from flask import Flask

try:
    from transaction_simulator import tx_simulator
    TX_SIMULATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Transaction simulator unavailable: {e}")
    TX_SIMULATOR_AVAILABLE = False
    
# Безопасный импорт модулей
try:
    import ton_manager
    from config import BOT_TOKEN, ADMIN_IDS, MIN_NFT_PRICE, MAX_NFT_PRICE, TON_NETWORK
    TON_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Config модули недоступны: {e}")
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
    ADMIN_IDS = [788630583]
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

# Инициализация бота
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

web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояния для отслеживания
waiting_for_wallet = {}
waiting_for_nft = {}
waiting_for_sale = {}
waiting_for_gift = {}

# Временное хранилище NFT (в реальном приложении - в базе данных)
user_nfts = {}

# Команды бота
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

@bot.message_handler(commands=['nft'])
def nft_command(message):
    """Создание NFT"""
    if not DB_AVAILABLE:
        bot.send_message(message.chat.id, "❌ База данных недоступна")
        return

    wallet_address = db.get_wallet_address(message.from_user.id)
    if not wallet_address:
        bot.send_message(message.chat.id, "❌ Сначала подключите кошелек через /connect")
        return

    nft_text = """
🎨 Создание NFT

Выберите тип NFT:

1. 🖼️ **Изображение** - загрузите картинку
2. 📹 **Видео** - короткое видео 
3. 🎵 **Аудио** - музыка или звук
4. 📝 **Текст** - уникальный текст

Отправьте мне файл или напишите текст для вашего NFT!
    """
    
    waiting_for_nft[message.chat.id] = True
    bot.send_message(message.chat.id, nft_text)

@bot.message_handler(commands=['my_nfts'])
def my_nfts_command(message):
    """Мои NFT"""
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "🖼️ У вас пока нет NFT\n\n🎨 Используйте /nft чтобы создать первую NFT!")
        return

    nfts_text = "🖼️ **Ваши NFT:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        nfts_text += f"{i}. **{nft['name']}**\n"
        nfts_text += f"   🆔 ID: {nft['id']}\n"
        nfts_text += f"   📅 Создан: {nft['created_at']}\n"
        nfts_text += f"   💰 Цена: {nft.get('price', 'Не продается')} TON\n"
        nfts_text += f"   👤 Владелец: Вы\n\n"

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💰 Продать NFT", callback_data="sell_nft_list")
    btn2 = types.InlineKeyboardButton("🎁 Подарить NFT", callback_data="gift_nft_list")
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, nfts_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['market'])
def market_command(message):
    """Маркетплейс NFT"""
    market_text = """
🏪 **NFT Маркетплейс**

Здесь будут доступны NFT для покупки!

Пока маркетплейс пуст, но скоро здесь появятся уникальные NFT от других пользователей!

🎨 Создайте свой первый NFT и выставьте его на продажу!
    """
    bot.send_message(message.chat.id, market_text, parse_mode='Markdown')

@bot.message_handler(commands=['sell'])
def sell_command(message):
    """Продажа NFT"""
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ У вас нет NFT для продажи")
        return

    sell_text = "💰 **Выберите NFT для продажи:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        sell_text += f"{i}. {nft['name']} (ID: {nft['id']})\n"

    sell_text += "\nОтправьте номер NFT который хотите продать:"
    
    waiting_for_sale[message.chat.id] = True
    bot.send_message(message.chat.id, sell_text)

@bot.message_handler(commands=['gift'])
def gift_command(message):
    """Подарок NFT"""
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ У вас нет NFT для подарка")
        return

    gift_text = "🎁 **Выберите NFT для подарка:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        gift_text += f"{i}. {nft['name']} (ID: {nft['id']})\n"

    gift_text += "\nОтправьте номер NFT который хотите подарить:"
    
    waiting_for_gift[message.chat.id] = True
    bot.send_message(message.chat.id, gift_text)

# В функции handle_gift_recipient после передачи NFT добавьте:
if TX_SIMULATOR_AVAILABLE:
    transaction = tx_simulator.simulate_gift(
        nft_id=nft_id,
        from_user=user_id,
        to_user=recipient_id
    )
    
    success_text = f"""
🎁 NFT успешно подарен!

🖼️ {gifted_nft['name']}
👤 Получатель: ID {recipient_id}
🔗 Транзакция: {transaction['tx_hash']}
💫 Подарок отправлен!

Теперь этот NFT принадлежит другому пользователю.
"""

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
/nft - Создать NFT
/my_nfts - Мои NFT
/sell - Продать NFT
/gift - Подарить NFT
/market - Маркетплейс

🎨 NFT функционал:
• Создание NFT из медиа
• Продажа NFT за TON
• Подарки NFT друзьям
• Просмотр коллекции
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['debug'])
def debug_command(message):
    """Отладочная информация"""
    user_id = message.from_user.id
    nft_count = len(user_nfts.get(user_id, []))
    
    debug_text = f"""
🔧 Системная информация:

🤖 Бот: Активен ✅
🌐 Хостинг: Render
🔑 Токен: Установлен ✅
💎 TON: {'✅ Доступен' if TON_AVAILABLE else '❌ Недоступен'}
🗃️ База данных: {'✅ Доступна' if DB_AVAILABLE else '❌ Недоступна'}
🖼️ Ваших NFT: {nft_count}

💡 Команды NFT:
/nft - Создать NFT
/my_nfts - Мои NFT  
/sell - Продать NFT
/gift - Подарить NFT
    """
    bot.send_message(message.chat.id, debug_text)

# Обработчики медиа для NFT
@bot.message_handler(content_types=['photo', 'video', 'audio', 'document'])
def handle_media(message):
    """Обработка медиа-файлов для NFT"""
    if waiting_for_nft.get(message.chat.id):
        user_id = message.from_user.id
        
        # Создаем NFT
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"NFT #{len(user_nfts.get(user_id, [])) + 1}"
        
        if user_id not in user_nfts:
            user_nfts[user_id] = []
        
        new_nft = {
            'id': nft_id,
            'name': nft_name,
            'type': 'media',
            'owner_id': user_id,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None,
            'for_sale': False
        }
        
        user_nfts[user_id].append(new_nft)
        waiting_for_nft[message.chat.id] = False
        
        success_text = f"""
🎉 NFT успешно создан!

🖼️ Название: {nft_name}
🆔 ID: {nft_id}
📅 Создан: {new_nft['created_at']}
👤 Владелец: Вы

Теперь вы можете:
• 💰 Продать этот NFT
• 🎁 Подарить его другу
• 🖼️ Посмотреть в своей коллекции
        """
        
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}")
        btn2 = types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
        btn3 = types.InlineKeyboardButton("🖼️ Коллекция", callback_data="my_nfts")
        markup.add(btn1, btn2, btn3)
        
        bot.send_message(message.chat.id, success_text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "📁 Чтобы создать NFT, сначала используйте команду /nft")

# Обработка текста для NFT
@bot.message_handler(func=lambda message: waiting_for_nft.get(message.chat.id) and message.text)
def handle_nft_text(message):
    """Обработка текста для NFT"""
    if len(message.text) > 5:
        user_id = message.from_user.id
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"Текст NFT #{len(user_nfts.get(user_id, [])) + 1}"
        
        if user_id not in user_nfts:
            user_nfts[user_id] = []
        
        new_nft = {
            'id': nft_id,
            'name': nft_name,
            'type': 'text',
            'content': message.text,
            'owner_id': user_id,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None,
            'for_sale': False
        }
        
        user_nfts[user_id].append(new_nft)
        waiting_for_nft[message.chat.id] = False
        
        success_text = f"""
🎉 Текстовый NFT успешно создан!

📝 Название: {nft_name}
🆔 ID: {nft_id}
📅 Создан: {new_nft['created_at']}
👤 Владелец: Вы

💬 Содержание:
{message.text}

Теперь вы можете:
• 💰 Продать этот NFT
• 🎁 Подарить его другу
• 🖼️ Посмотреть в своей коллекции
        """
        
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}")
        btn2 = types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
        btn3 = types.InlineKeyboardButton("🖼️ Коллекция", callback_data="my_nfts")
        markup.add(btn1, btn2, btn3)
        
        bot.send_message(message.chat.id, success_text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Текст слишком короткий для NFT. Нужно минимум 5 символов.")

# Обработка продажи NFT
@bot.message_handler(func=lambda message: waiting_for_sale.get(message.chat.id))
def handle_sale_selection(message):
    """Обработка выбора NFT для продажи"""
    try:
        user_id = message.from_user.id
        nft_index = int(message.text) - 1
        
        if user_id in user_nfts and 0 <= nft_index < len(user_nfts[user_id]):
            nft = user_nfts[user_id][nft_index]
            waiting_for_sale[message.chat.id] = nft['id']
            
            price_text = f"""
💰 Продажа NFT: {nft['name']}

Введите цену в TON (от {MIN_NFT_PRICE} до {MAX_NFT_PRICE} TON):

Пример: 1.5
            """
            bot.send_message(message.chat.id, price_text)
        else:
            bot.send_message(message.chat.id, "❌ Неверный номер NFT")
            waiting_for_sale[message.chat.id] = False
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число")
        waiting_for_sale[message.chat.id] = False

# Обработка цены для продажи
@bot.message_handler(func=lambda message: waiting_for_sale.get(message.chat.id) and isinstance(waiting_for_sale[message.chat.id], str))
def handle_sale_price(message):
    """Обработка цены для продажи NFT"""
    try:
        price = float(message.text)
        if MIN_NFT_PRICE <= price <= MAX_NFT_PRICE:
            nft_id = waiting_for_sale[message.chat.id]
            user_id = message.from_user.id

            # В функции handle_sale_price после установки цены добавьте:
if TX_SIMULATOR_AVAILABLE:
    transaction = tx_simulator.simulate_sale(
        nft_id=nft_id,
        seller_id=user_id,
        buyer_id=None,  # пока нет покупателя
        price=price
    )
    
    success_text = f"""
✅ NFT выставлен на продажу!

🖼️ {nft['name']}
💰 Цена: {price} TON
📊 Статус: В продаже
🔗 Транзакция: {transaction['tx_hash']}

Теперь ваш NFT виден в маркетплейсе!
"""
            
            # Находим NFT и устанавливаем цену
            for nft in user_nfts.get(user_id, []):
                if nft['id'] == nft_id:
                    nft['price'] = price
                    nft['for_sale'] = True
                    break
            
            success_text = f"""
✅ NFT выставлен на продажу!

🖼️ {nft['name']}
💰 Цена: {price} TON
📊 Статус: В продаже

Теперь ваш NFT виден в маркетплейсе!
            """
            bot.send_message(message.chat.id, success_text)
        else:
            bot.send_message(message.chat.id, f"❌ Цена должна быть от {MIN_NFT_PRICE} до {MAX_NFT_PRICE} TON")
    
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число (например: 1.5)")
    
    waiting_for_sale[message.chat.id] = False

# Обработка подарка NFT
@bot.message_handler(func=lambda message: waiting_for_gift.get(message.chat.id))
def handle_gift_selection(message):
    """Обработка выбора NFT для подарка"""
    try:
        user_id = message.from_user.id
        nft_index = int(message.text) - 1
        
        if user_id in user_nfts and 0 <= nft_index < len(user_nfts[user_id]):
            nft = user_nfts[user_id][nft_index]
            waiting_for_gift[message.chat.id] = nft['id']
            
            gift_text = f"""
🎁 Подарок NFT: {nft['name']}

Введите ID пользователя Telegram, которому хотите подарить этот NFT:

Пример: 123456789
            """
            bot.send_message(message.chat.id, gift_text)
        else:
            bot.send_message(message.chat.id, "❌ Неверный номер NFT")
            waiting_for_gift[message.chat.id] = False
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число")
        waiting_for_gift[message.chat.id] = False

# Обработка получателя подарка
@bot.message_handler(func=lambda message: waiting_for_gift.get(message.chat.id) and isinstance(waiting_for_gift[message.chat.id], str))
def handle_gift_recipient(message):
    """Обработка получателя подарка"""
    try:
        recipient_id = int(message.text)
        nft_id = waiting_for_gift[message.chat.id]
        user_id = message.from_user.id
        
        # Находим NFT и передаем другому пользователю
        for i, nft in enumerate(user_nfts.get(user_id, [])):
            if nft['id'] == nft_id:
                gifted_nft = user_nfts[user_id].pop(i)
                gifted_nft['owner_id'] = recipient_id
                
                if recipient_id not in user_nfts:
                    user_nfts[recipient_id] = []
                user_nfts[recipient_id].append(gifted_nft)
                
                success_text = f"""
🎁 NFT успешно подарен!

🖼️ {gifted_nft['name']}
👤 Получатель: ID {recipient_id}
💫 Подарок отправлен!

Теперь этот NFT принадлежит другому пользователю.
                """
                bot.send_message(message.chat.id, success_text)
                break
        else:
            bot.send_message(message.chat.id, "❌ NFT не найден")
    
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите числовой ID пользователя")
    
    waiting_for_gift[message.chat.id] = False

# Обработка ввода адреса кошелька
@bot.message_handler(func=lambda message: waiting_for_wallet.get(message.chat.id))
def handle_wallet_address(message):
    """Обработка адреса кошелька"""
    wallet_address = message.text.strip()
    
    if wallet_address.startswith(('EQ', 'UQ', '0Q')) and len(wallet_address) >= 48:
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
    
    waiting_for_wallet[message.chat.id] = False

# Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    """Обработка inline кнопок"""
    user_id = call.from_user.id
    
    if call.data == "sell_nft_list":
        sell_command(call.message)
    elif call.data == "gift_nft_list":
        gift_command(call.message)
    elif call.data == "my_nfts":
        my_nfts_command(call.message)
    elif call.data.startswith("sell_"):
        nft_id = call.data[5:]
        waiting_for_sale[call.message.chat.id] = nft_id
        price_text = f"💰 Введите цену в TON для NFT {nft_id}:"
        bot.send_message(call.message.chat.id, price_text)
    elif call.data.startswith("gift_"):
        nft_id = call.data[5:]
        waiting_for_gift[call.message.chat.id] = nft_id
        gift_text = f"🎁 Введите ID пользователя для подарка NFT {nft_id}:"
        bot.send_message(call.message.chat.id, gift_text)
    
    bot.answer_callback_query(call.id)

# Обработка кнопок главного меню
def echo_message(message):
    """Эхо-ответ для тестирования"""
    if message.text == '🟢 Статус':
        bot.send_message(message.chat.id, f"✅ Бот работает стабильно!\nХостинг: Render\nTON: {'✅' if TON_AVAILABLE else '⚠️'}\nБаза данных: {'✅' if DB_AVAILABLE else '❌'}")
    elif message.text == 'ℹ️ Помощь':
        help_command(message)
    elif message.text == '💎 TON':
        ton_text = "💎 TON интеграция готовится! Скоро будут реальные транзакции!" if TON_AVAILABLE else "⚠️ TON временно недоступен"
        bot.send_message(message.chat.id, ton_text)
    elif message.text == '👛 Мой кошелек':
        my_wallet_command(message)
    elif message.text == '🎨 Создать NFT':
        nft_command(message)
    elif message.text == '🖼️ Мои NFT':
        my_nfts_command(message)
    elif message.text == '💰 Продать NFT':
        sell_command(message)
    elif message.text == '🎁 Подарить NFT':
        gift_command(message)
    elif message.text == '🏪 Маркетплейс':
        market_command(message)
    else:
        bot.reply_to(message, f"🔍 Получено сообщение: {message.text}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех сообщений"""
    if waiting_for_wallet.get(message.chat.id):
        handle_wallet_address(message)
    elif waiting_for_nft.get(message.chat.id) and message.text:
        handle_nft_text(message)
    elif waiting_for_sale.get(message.chat.id):
        if isinstance(waiting_for_sale[message.chat.id], bool):
            handle_sale_selection(message)
        else:
            handle_sale_price(message)
    elif waiting_for_gift.get(message.chat.id):
        if isinstance(waiting_for_gift[message.chat.id], bool):
            handle_gift_selection(message)
        else:
            handle_gift_recipient(message)
    else:
        echo_message(message)

if __name__ == "__main__":
    logger.info("🤖 Запуск NFT бота с маркетплейсом...")
    logger.info(f"💎 TON доступен: {TON_AVAILABLE}")
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






