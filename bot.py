import os
import logging
import time
import random
from datetime import datetime
from telebot import TeleBot, types

# === КОНФИГУРАЦИЯ ===
from config import BOT_TOKEN, MIN_NFT_PRICE, MAX_NFT_PRICE
from database import DatabaseManager
from transaction_simulator import tx_simulator

# Инициализация
bot = TeleBot(BOT_TOKEN)
db = DatabaseManager()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
waiting_for = {
    'wallet': {}, 'nft': {}, 'sale': {}, 'gift': {}, 'price': {}, 'recipient': {}
}
user_nfts = {}
nft_marketplace = []

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    welcome_text = f"""
🎨 Привет, {user.first_name}!

Я бот для создания и торговли NFT в сети TON!

✨ Создавай, продавай и дари NFT!
✅ Все системы работают

🚀 Версия: 3.0 (Full NFT Bot)
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        '🟢 Статус', 'ℹ️ Помощь', '💎 TON',
        '👛 Кошелек', '🎨 Создать NFT', '🖼️ Мои NFT',
        '💰 Продать', '🎁 Подарить', '🏪 Маркет',
        '📊 Транзакции', '🔄 Обновить'
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📋 **Доступные команды:**

/start - Главное меню
/help - Справка
/nft - Создать NFT
/my_nfts - Мои NFT
/sell - Продать NFT
/gift - Подарить NFT
/market - Маркетплейс
/transactions - История транзакций
/connect - Подключить кошелек

🎨 **Функции:**
• Создание NFT из фото/видео/текста
• Продажа NFT за TON
• Подарки NFT друзьям
• История транзакций
• Маркетплейс
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['nft'])
def nft_command(message):
    nft_text = """
🎨 **Создание NFT**

Выберите тип:
• 📸 Фото - отправьте изображение
• 🎥 Видео - отправьте видео
• 📝 Текст - напишите текст

Создайте свою первую NFT коллекцию!
    """
    waiting_for['nft'][message.chat.id] = True
    bot.send_message(message.chat.id, nft_text, parse_mode='Markdown')

@bot.message_handler(commands=['my_nfts'])
def my_nfts_command(message):
    user_id = message.from_user.id
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "🖼️ У вас пока нет NFT!\nИспользуйте /nft чтобы создать первый NFT.")
        return
    
    nfts_text = "🖼️ **Ваша NFT коллекция:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        nfts_text += f"{i}. **{nft['name']}**\n"
        nfts_text += f"   🆔 {nft['id']}\n"
        nfts_text += f"   📅 {nft['created_at']}\n"
        if nft.get('price'):
            nfts_text += f"   💰 {nft['price']} TON\n"
        nfts_text += "\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💰 Продать NFT", callback_data="sell_nft"),
        types.InlineKeyboardButton("🎁 Подарить NFT", callback_data="gift_nft")
    )
    bot.send_message(message.chat.id, nfts_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['sell'])
def sell_command(message):
    user_id = message.from_user.id
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ У вас нет NFT для продажи")
        return
    
    sell_text = "💰 **Выберите NFT для продажи:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        sell_text += f"{i}. {nft['name']}\n"
    
    sell_text += f"\nОтправьте номер NFT (1-{len(user_nfts[user_id])}):"
    waiting_for['sale'][message.chat.id] = True
    bot.send_message(message.chat.id, sell_text, parse_mode='Markdown')

@bot.message_handler(commands=['gift'])
def gift_command(message):
    user_id = message.from_user.id
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ У вас нет NFT для подарка")
        return
    
    gift_text = "🎁 **Выберите NFT для подарка:**\n\n"
    for i, nft in enumerate(user_nfts[user_id], 1):
        gift_text += f"{i}. {nft['name']}\n"
    
    gift_text += f"\nОтправьте номер NFT (1-{len(user_nfts[user_id])}):"
    waiting_for['gift'][message.chat.id] = True
    bot.send_message(message.chat.id, gift_text, parse_mode='Markdown')

@bot.message_handler(commands=['market'])
def market_command(message):
    if not nft_marketplace:
        market_text = "🏪 **NFT Маркетплейс**\n\nПока нет NFT в продаже.\n\nСоздайте свой первый NFT и выставьте его на продажу!"
    else:
        market_text = "🏪 **NFT Маркетплейс**\n\n"
        for i, nft in enumerate(nft_marketplace, 1):
            market_text += f"{i}. **{nft['name']}**\n"
            market_text += f"   💰 {nft['price']} TON\n"
            market_text += f"   👤 Продавец: {nft['owner_name']}\n\n"
    
    bot.send_message(message.chat.id, market_text, parse_mode='Markdown')

@bot.message_handler(commands=['transactions'])
def transactions_command(message):
    user_id = message.from_user.id
    transactions = tx_simulator.get_user_transactions(user_id)
    
    if not transactions:
        tx_text = "📊 **История транзакций**\n\nУ вас пока нет транзакций."
    else:
        tx_text = "📊 **Ваши транзакции:**\n\n"
        for tx in transactions[-5:]:  # Последние 5 транзакций
            tx_text += f"🔗 {tx['tx_hash']}\n"
            tx_text += f"   📝 {tx['type'].upper()}\n"
            tx_text += f"   💰 {tx['amount']} TON\n"
            tx_text += f"   📅 {tx['timestamp']}\n\n"
    
    bot.send_message(message.chat.id, tx_text, parse_mode='Markdown')

@bot.message_handler(commands=['connect'])
def connect_wallet_command(message):
    help_text = """
💎 **Подключение TON кошелька**

Отправьте адрес вашего TON кошелька.

📝 Формат: EQ... или UQ... (48+ символов)

Пример:
`EQDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`
    """
    waiting_for['wallet'][message.chat.id] = True
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# === ОБРАБОТЧИКИ МЕДИА ===
@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_media(message):
    if waiting_for['nft'].get(message.chat.id):
        user_id = message.from_user.id
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"NFT #{len(user_nfts.get(user_id, [])) + 1}"
        
        if user_id not in user_nfts:
            user_nfts[user_id] = []
        
        nft_type = 'photo' if message.photo else 'video' if message.video else 'document'
        new_nft = {
            'id': nft_id, 'name': nft_name, 'type': nft_type,
            'owner_id': user_id, 'owner_name': message.from_user.first_name,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None, 'for_sale': False
        }
        
        user_nfts[user_id].append(new_nft)
        waiting_for['nft'][message.chat.id] = False
        
        # Симуляция транзакции
        tx = tx_simulator.simulate_mint(nft_id, user_id)
        
        success_text = f"""
🎉 **NFT успешно создан!**

🖼️ **{nft_name}**
🆔 `{nft_id}`
📅 {new_nft['created_at']}
🔗 Транзакция: `{tx['tx_hash']}`

Ваш NFT добавлен в коллекцию!
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
            types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}"),
            types.InlineKeyboardButton("🖼️ Коллекция", callback_data="my_nfts")
        )
        
        bot.send_message(message.chat.id, success_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: waiting_for['nft'].get(message.chat.id) and message.text)
def handle_nft_text(message):
    if len(message.text) > 3:
        user_id = message.from_user.id
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"Текст NFT #{len(user_nfts.get(user_id, [])) + 1}"
        
        if user_id not in user_nfts:
            user_nfts[user_id] = []
        
        new_nft = {
            'id': nft_id, 'name': nft_name, 'type': 'text',
            'content': message.text, 'owner_id': user_id,
            'owner_name': message.from_user.first_name,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None, 'for_sale': False
        }
        
        user_nfts[user_id].append(new_nft)
        waiting_for['nft'][message.chat.id] = False
        
        # Симуляция транзакции
        tx = tx_simulator.simulate_mint(nft_id, user_id)
        
        success_text = f"""
🎉 **Текстовый NFT создан!**

📝 **{nft_name}**
🆔 `{nft_id}`
📅 {new_nft['created_at']}
🔗 Транзакция: `{tx['tx_hash']}`

💬 Содержание:
{message.text}
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
            types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}"),
            types.InlineKeyboardButton("🖼️ Коллекция", callback_data="my_nfts")
        )
        
        bot.send_message(message.chat.id, success_text, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Текст слишком короткий. Нужно минимум 4 символа.")

# === ОБРАБОТЧИКИ ПРОДАЖИ ===
@bot.message_handler(func=lambda message: waiting_for['sale'].get(message.chat.id))
def handle_sale_selection(message):
    try:
        user_id = message.from_user.id
        nft_index = int(message.text) - 1
        
        if user_id in user_nfts and 0 <= nft_index < len(user_nfts[user_id]):
            nft = user_nfts[user_id][nft_index]
            waiting_for['sale'][message.chat.id] = False
            waiting_for['price'][message.chat.id] = nft['id']
            
            price_text = f"""
💰 **Продажа NFT: {nft['name']}**

Введите цену в TON:
💎 Минимум: {MIN_NFT_PRICE} TON
💎 Максимум: {MAX_NFT_PRICE} TON

Пример: 2.5
            """
            bot.send_message(message.chat.id, price_text, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Неверный номер NFT")
            waiting_for['sale'][message.chat.id] = False
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число")
        waiting_for['sale'][message.chat.id] = False

@bot.message_handler(func=lambda message: waiting_for['price'].get(message.chat.id))
def handle_sale_price(message):
    try:
        price = float(message.text)
        if MIN_NFT_PRICE <= price <= MAX_NFT_PRICE:
            nft_id = waiting_for['price'][message.chat.id]
            user_id = message.from_user.id
            
            # Находим NFT и устанавливаем цену
            for nft in user_nfts[user_id]:
                if nft['id'] == nft_id:
                    nft['price'] = price
                    nft['for_sale'] = True
                    
                    # Добавляем в маркетплейс
                    if nft not in nft_marketplace:
                        nft_marketplace.append(nft)
                    
                    # Симуляция транзакции
                    tx = tx_simulator.simulate_sale(nft_id, user_id, price)
                    
                    success_text = f"""
✅ **NFT выставлен на продажу!**

🖼️ **{nft['name']}**
💰 **Цена:** {price} TON
🔗 **Транзакция:** `{tx['tx_hash']}`
📊 **Статус:** В продаже

Теперь ваш NFT виден в маркетплейсе!
                    """
                    bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
                    break
        else:
            bot.send_message(message.chat.id, f"❌ Цена должна быть от {MIN_NFT_PRICE} до {MAX_NFT_PRICE} TON")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число (например: 1.5)")
    
    waiting_for['price'][message.chat.id] = False

# === ОБРАБОТЧИКИ ПОДАРКОВ ===
@bot.message_handler(func=lambda message: waiting_for['gift'].get(message.chat.id))
def handle_gift_selection(message):
    try:
        user_id = message.from_user.id
        nft_index = int(message.text) - 1
        
        if user_id in user_nfts and 0 <= nft_index < len(user_nfts[user_id]):
            nft = user_nfts[user_id][nft_index]
            waiting_for['gift'][message.chat.id] = False
            waiting_for['recipient'][message.chat.id] = nft['id']
            
            gift_text = f"""
🎁 **Подарок NFT: {nft['name']}**

Введите ID пользователя Telegram:

Пример: 123456789
            """
            bot.send_message(message.chat.id, gift_text, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Неверный номер NFT")
            waiting_for['gift'][message.chat.id] = False
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число")
        waiting_for['gift'][message.chat.id] = False

@bot.message_handler(func=lambda message: waiting_for['recipient'].get(message.chat.id))
def handle_gift_recipient(message):
    try:
        recipient_id = int(message.text)
        nft_id = waiting_for['recipient'][message.chat.id]
        user_id = message.from_user.id
        
        # Находим NFT и передаем другому пользователю
        for i, nft in enumerate(user_nfts[user_id]):
            if nft['id'] == nft_id:
                gifted_nft = user_nfts[user_id].pop(i)
                gifted_nft['owner_id'] = recipient_id
                gifted_nft['owner_name'] = f"User_{recipient_id}"
                gifted_nft['for_sale'] = False
                gifted_nft['price'] = None
                
                # Убираем из маркетплейса если был там
                if gifted_nft in nft_marketplace:
                    nft_marketplace.remove(gifted_nft)
                
                if recipient_id not in user_nfts:
                    user_nfts[recipient_id] = []
                user_nfts[recipient_id].append(gifted_nft)
                
                # Симуляция транзакции
                tx = tx_simulator.simulate_gift(nft_id, user_id, recipient_id)
                
                success_text = f"""
🎁 **NFT успешно подарен!**

🖼️ **{gifted_nft['name']}**
👤 **Получатель:** ID {recipient_id}
🔗 **Транзакция:** `{tx['tx_hash']}`
💫 **Статус:** Подарок отправлен!

Теперь этот NFT принадлежит другому пользователю.
                """
                bot.send_message(message.chat.id, success_text, parse_mode='Markdown')
                break
        else:
            bot.send_message(message.chat.id, "❌ NFT не найден")
    
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите числовой ID пользователя")
    
    waiting_for['recipient'][message.chat.id] = False

# === ОБРАБОТЧИК КОШЕЛЬКА ===
@bot.message_handler(func=lambda message: waiting_for['wallet'].get(message.chat.id))
def handle_wallet_address(message):
    wallet_address = message.text.strip()
    
    if wallet_address.startswith(('EQ', 'UQ', '0Q')) and len(wallet_address) >= 48:
        success = db.save_wallet_address(
            user_id=message.from_user.id,
            username=message.from_user.username or f"user_{message.from_user.id}",
            wallet_address=wallet_address
        )

        if success:
            bot.send_message(message.chat.id, f"✅ **Кошелек подключен!**\n\n📍 Адрес: `{wallet_address}`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения кошелька")
    else:
        bot.send_message(message.chat.id, "❌ Неверный формат TON адреса")
    
    waiting_for['wallet'][message.chat.id] = False

# === INLINE КНОПКИ ===
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    if call.data == "sell_nft":
        sell_command(call.message)
    elif call.data == "gift_nft":
        gift_command(call.message)
    elif call.data == "my_nfts":
        my_nfts_command(call.message)
    elif call.data.startswith("sell_"):
        nft_id = call.data[5:]
        waiting_for['price'][call.message.chat.id] = nft_id
        bot.send_message(call.message.chat.id, f"💰 Введите цену в TON для NFT {nft_id}:")
    elif call.data.startswith("gift_"):
        nft_id = call.data[5:]
        waiting_for['recipient'][call.message.chat.id] = nft_id
        bot.send_message(call.message.chat.id, f"🎁 Введите ID пользователя для подарка NFT {nft_id}:")
    
    bot.answer_callback_query(call.id)

# === ГЛАВНОЕ МЕНЮ ===
@bot.message_handler(func=lambda message: True)
def handle_main_menu(message):
    text = message.text
    
    if text == '🟢 Статус':
        user_id = message.from_user.id
        nft_count = len(user_nfts.get(user_id, []))
        status_text = f"""
🟢 **Статус бота:** Активен
🖼️ **Ваших NFT:** {nft_count}
🏪 **В маркетплейсе:** {len(nft_marketplace)}
💎 **Режим:** Демо (TON скоро)
        """
        bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    
    elif text == 'ℹ️ Помощь':
        help_command(message)
    
    elif text == '💎 TON':
        bot.send_message(message.chat.id, "💎 **TON интеграция**\n\nРеальные транзакции появятся в следующем обновлении! Сейчас работаем в демо-режиме.", parse_mode='Markdown')
    
    elif text == '👛 Кошелек':
        connect_wallet_command(message)
    
    elif text == '🎨 Создать NFT':
        nft_command(message)
    
    elif text == '🖼️ Мои NFT':
        my_nfts_command(message)
    
    elif text == '💰 Продать':
        sell_command(message)
    
    elif text == '🎁 Подарить':
        gift_command(message)
    
    elif text == '🏪 Маркет':
        market_command(message)
    
    elif text == '📊 Транзакции':
        transactions_command(message)
    
    elif text == '🔄 Обновить':
        bot.send_message(message.chat.id, "🔄 **Бот обновлен!**\n\nВсе функции активны и готовы к работе! 🎉", parse_mode='Markdown')
    
    else:
        bot.send_message(message.chat.id, "🤖 Используйте кнопки меню для навигации!")

# === ЗАПУСК ===
if __name__ == "__main__":
    print("🚀 NFT Bot starting...")
    logger.info("🤖 NFT Bot launched successfully!")
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            time.sleep(15)
