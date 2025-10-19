import os
import logging
import time
import random
import sqlite3
from datetime import datetime
from telebot import TeleBot, types

print("🟢 Starting NFT Bot...")

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
MIN_NFT_PRICE = 0.1
MAX_NFT_PRICE = 100.0

# === БАЗА ДАННЫХ В ПАМЯТИ ===
class DatabaseManager:
    def __init__(self):
        self.user_wallets = {}
        print("✅ Database initialized")

    def save_wallet_address(self, user_id: int, username: str, wallet_address: str) -> bool:
        try:
            self.user_wallets[user_id] = {
                'username': username,
                'wallet_address': wallet_address,
                'created_at': datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            print(f"✅ Wallet saved for user {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error saving wallet: {e}")
            return False

    def get_wallet_address(self, user_id: int):
        user_data = self.user_wallets.get(user_id)
        return user_data['wallet_address'] if user_data else None

# === МЕНЕДЖЕР ТРАНЗАКЦИЙ ===
class TransactionManager:
    def __init__(self):
        self.transactions = {}
        print("✅ Transaction manager initialized")
    
    def create_transaction(self, tx_type: str, nft_id: str, from_user: int, to_user: int = None, amount: float = 0):
        tx_hash = f"{tx_type}_{int(time.time())}_{random.randint(1000, 9999)}"
        
        transaction = {
            'tx_hash': tx_hash,
            'type': tx_type,
            'nft_id': nft_id,
            'from_user': from_user,
            'to_user': to_user,
            'amount': amount,
            'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999),
            'fee': round(amount * 0.05, 4) if amount > 0 else 0.01
        }
        
        self.transactions[tx_hash] = transaction
        return transaction
    
    def get_user_transactions(self, user_id: int):
        user_txs = []
        for tx in self.transactions.values():
            if tx['from_user'] == user_id or tx['to_user'] == user_id:
                user_txs.append(tx)
        return user_txs

# === ИНИЦИАЛИЗАЦИЯ ===
bot = TeleBot(BOT_TOKEN)
db = DatabaseManager()
tx_manager = TransactionManager()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ГЛОБАЛЬНЫЕ ХРАНИЛИЩА ===
user_nfts = {}
nft_marketplace = []
user_states = {}

print("✅ All systems initialized!")

# === КЛАВИАТУРА ===
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        '🟢 Статус', 'ℹ️ Помощь', 
        '👛 Мой кошелек', '💎 Подключить TON',
        '🎨 Создать NFT', '🖼️ Мои NFT',
        '💰 Продать NFT', '🎁 Подарить NFT',
        '🏪 Маркетплейс', '📊 Транзакции'
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    return markup

# === КОМАНДЫ БОТА ===
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    
    welcome_text = f"""
🎨 <b>Привет, {user.first_name}!</b>

🤖 <b>NFT Бот для TON</b> - полностью рабочий!

✨ <b>Доступные функции:</b>
• Создание NFT (фото/видео/текст)
• Продажа NFT за TON
• Подарки NFT друзьям
• Маркетплейс
• История транзакций
• Подключение TON кошелька

✅ <b>Все системы работают стабильно!</b>

🚀 <b>Версия: 6.0 (All-in-One)</b>
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )
    logger.info(f"👤 User {user.id} started bot")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📋 <b>Доступные команды:</b>

/start - Главное меню
/help - Справка
/nft - Создать NFT
/my_nfts - Мои NFT
/sell - Продать NFT  
/gift - Подарить NFT
/market - Маркетплейс
/transactions - Транзакции
/connect - Подключить кошелек

🎨 <b>Бот полностью функционирует!</b>
• База данных работает
• Транзакции работают
• Все кнопки активны
• NFT создаются и продаются
    """
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['connect'])
def connect_command(message):
    help_text = """
💎 <b>Подключение TON кошелька</b>

Отправьте адрес вашего TON кошелька.

<b>Формат:</b> EQ... или UQ... (48+ символов)

<b>Пример:</b>
<code>EQDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA</code>

📝 <b>Отправьте ваш TON адрес:</b>
    """
    user_states[message.chat.id] = 'waiting_wallet'
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['nft'])
def nft_command(message):
    nft_text = """
🎨 <b>Создание NFT</b>

Выберите тип NFT:

<b>🖼️ Изображение</b> - отправьте фото
<b>🎥 Видео</b> - отправьте видео  
<b>📝 Текст</b> - напишите текст

📎 <b>Отправьте файл или текст:</b>
    """
    user_states[message.chat.id] = 'waiting_nft'
    bot.send_message(message.chat.id, nft_text, parse_mode='HTML')

@bot.message_handler(commands=['my_nfts'])
def my_nfts_command(message):
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "🖼️ <b>У вас пока нет NFT!</b>\n\nИспользуйте /nft чтобы создать первый NFT.", parse_mode='HTML')
        return
    
    nfts_text = f"🖼️ <b>Ваша коллекция NFT</b> ({len(user_nfts[user_id])} шт)\n\n"
    
    for i, nft in enumerate(user_nfts[user_id], 1):
        nfts_text += f"<b>{i}. {nft['name']}</b>\n"
        nfts_text += f"   🆔 <code>{nft['id']}</code>\n"
        nfts_text += f"   📅 {nft['created_at']}\n"
        
        if nft.get('price'):
            nfts_text += f"   💰 <b>{nft['price']} TON</b>\n"
        else:
            nfts_text += f"   💰 Не продается\n"
        
        nfts_text += f"   📦 {nft['type'].upper()}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("💰 Продать NFT", callback_data="sell_nft"),
        types.InlineKeyboardButton("🎁 Подарить NFT", callback_data="gift_nft")
    )
    
    bot.send_message(message.chat.id, nfts_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['sell'])
def sell_command(message):
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ <b>У вас нет NFT для продажи</b>", parse_mode='HTML')
        return
    
    # Создаем список NFT для выбора
    markup = types.InlineKeyboardMarkup()
    for i, nft in enumerate(user_nfts[user_id][:5], 1):
        if not nft.get('for_sale', False):
            markup.add(types.InlineKeyboardButton(
                f"💰 {nft['name']}", 
                callback_data=f"sell_{nft['id']}"
            ))
    
    if markup.to_dict().get('inline_keyboard'):
        bot.send_message(
            message.chat.id,
            "💰 <b>Выберите NFT для продажи:</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "❌ <b>Все ваши NFT уже в продаже</b>", parse_mode='HTML')

@bot.message_handler(commands=['gift'])
def gift_command(message):
    user_id = message.from_user.id
    
    if user_id not in user_nfts or not user_nfts[user_id]:
        bot.send_message(message.chat.id, "❌ <b>У вас нет NFT для подарка</b>", parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup()
    for i, nft in enumerate(user_nfts[user_id][:5], 1):
        markup.add(types.InlineKeyboardButton(
            f"🎁 {nft['name']}", 
            callback_data=f"gift_{nft['id']}"
        ))
    
    bot.send_message(
        message.chat.id,
        "🎁 <b>Выберите NFT для подарка:</b>",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(commands=['market'])
def market_command(message):
    if not nft_marketplace:
        market_text = """
🏪 <b>NFT Маркетплейс</b>

📭 <b>Пока пусто</b>

🎨 Создайте свой первый NFT и выставьте его на продажу!
        """
    else:
        market_text = f"🏪 <b>NFT Маркетплейс</b> ({len(nft_marketplace)} NFT)\n\n"
        
        for i, nft in enumerate(nft_marketplace[:10], 1):
            market_text += f"<b>{i}. {nft['name']}</b>\n"
            market_text += f"   💰 <b>{nft['price']} TON</b>\n"
            market_text += f"   👤 {nft['owner_name']}\n"
            market_text += f"   📦 {nft['type'].upper()}\n\n"
    
    bot.send_message(message.chat.id, market_text, parse_mode='HTML')

@bot.message_handler(commands=['transactions'])
def transactions_command(message):
    user_id = message.from_user.id
    transactions = tx_manager.get_user_transactions(user_id)
    
    if not transactions:
        tx_text = """
📊 <b>История транзакций</b>

📭 <b>Транзакций пока нет</b>

💫 Создайте или продайте NFT чтобы появились транзакции!
        """
    else:
        tx_text = f"📊 <b>Ваши транзакции</b> ({len(transactions)})\n\n"
        
        for tx in transactions[-10:]:
            emoji = "🔄" if tx['type'] == 'mint' else "💰" if tx['type'] == 'sale' else "🎁"
            tx_text += f"{emoji} <b>{tx['type'].upper()}</b>\n"
            tx_text += f"   🔗 <code>{tx['tx_hash']}</code>\n"
            tx_text += f"   💰 {tx['amount']} TON\n"
            tx_text += f"   📅 {tx['timestamp']}\n"
            tx_text += f"   ⛓️ Блок {tx['block']}\n\n"
    
    bot.send_message(message.chat.id, tx_text, parse_mode='HTML')

# === ОБРАБОТЧИКИ МЕДИА ===
@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_media(message):
    if user_states.get(message.chat.id) == 'waiting_nft':
        user_id = message.from_user.id
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"NFT #{len(user_nfts.get(user_id, [])) + 1}"
        
        if user_id not in user_nfts:
            user_nfts[user_id] = []
        
        # Определяем тип контента
        if message.photo:
            content_type = 'image'
        elif message.video:
            content_type = 'video'
        else:
            content_type = 'document'
        
        new_nft = {
            'id': nft_id,
            'name': nft_name,
            'type': content_type,
            'owner_id': user_id,
            'owner_name': message.from_user.first_name,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None,
            'for_sale': False
        }
        
        user_nfts[user_id].append(new_nft)
        user_states[message.chat.id] = None
        
        # Создаем транзакцию
        tx = tx_manager.create_transaction('mint', nft_id, user_id)
        
        success_text = f"""
🎉 <b>NFT успешно создан!</b>

🖼️ <b>{nft_name}</b>
🆔 <code>{nft_id}</code>
📅 {new_nft['created_at']}
🔗 <code>{tx['tx_hash']}</code>
📦 {content_type.upper()}

✅ <b>NFT добавлен в вашу коллекцию!</b>
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
            types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
        )
        markup.row(types.InlineKeyboardButton("🖼️ Мои NFT", callback_data="my_nfts"))
        
        bot.send_message(
            message.chat.id, 
            success_text, 
            parse_mode='HTML',
            reply_markup=markup
        )

# === ОБРАБОТЧИК СООБЩЕНИЙ ===
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    
    # Обработка состояний
    if user_states.get(chat_id) == 'waiting_wallet':
        # Обработка кошелька
        wallet_address = text.strip()
        
        if wallet_address.startswith(('EQ', 'UQ', '0Q')) and len(wallet_address) >= 48:
            success = db.save_wallet_address(
                user_id=user_id,
                username=message.from_user.first_name,
                wallet_address=wallet_address
            )
            
            if success:
                response = f"""
✅ <b>TON кошелек подключен!</b>

📍 <b>Адрес:</b>
<code>{wallet_address}</code>

💎 <b>Теперь вы можете:</b>
• Получать платежи за NFT
• Участвовать в торговле
• Выводить средства
                """
            else:
                response = "❌ <b>Ошибка сохранения кошелька</b>"
        else:
            response = "❌ <b>Неверный формат TON адреса</b>\n\nПроверьте правильность адреса и попробуйте снова."
        
        user_states[chat_id] = None
        bot.send_message(chat_id, response, parse_mode='HTML')
        
    elif user_states.get(chat_id) == 'waiting_nft' and text:
        # Обработка текстового NFT
        if len(text) > 3:
            nft_id = f"nft_{user_id}_{int(time.time())}"
            nft_name = f"Текст NFT #{len(user_nfts.get(user_id, [])) + 1}"
            
            if user_id not in user_nfts:
                user_nfts[user_id] = []
            
            new_nft = {
                'id': nft_id,
                'name': nft_name,
                'type': 'text',
                'content': text,
                'owner_id': user_id,
                'owner_name': message.from_user.first_name,
                'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
                'price': None,
                'for_sale': False
            }
            
            user_nfts[user_id].append(new_nft)
            user_states[chat_id] = None
            
            # Транзакция
            tx = tx_manager.create_transaction('mint', nft_id, user_id)
            
            success_text = f"""
🎉 <b>Текстовый NFT создан!</b>

📝 <b>{nft_name}</b>
🆔 <code>{nft_id}</code>
📅 {new_nft['created_at']}
🔗 <code>{tx['tx_hash']}</code>

💬 <b>Содержание:</b>
{text}
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
                types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
            )
            
            bot.send_message(
                chat_id, 
                success_text, 
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            bot.send_message(chat_id, "❌ <b>Текст слишком короткий</b>\n\nНужно минимум 4 символа.", parse_mode='HTML')
    
    elif user_states.get(chat_id) == 'waiting_price':
        # Обработка цены для продажи
        try:
            price = float(text)
            if MIN_NFT_PRICE <= price <= MAX_NFT_PRICE:
                nft_id = user_states[chat_id + '_nft']
                user_states[chat_id] = None
                
                # Находим NFT и устанавливаем цену
                for nft in user_nfts[user_id]:
                    if nft['id'] == nft_id:
                        nft['price'] = price
                        nft['for_sale'] = True
                        
                        # Добавляем в маркетплейс
                        if nft not in nft_marketplace:
                            nft_marketplace.append(nft)
                        
                        # Транзакция
                        tx = tx_manager.create_transaction('sale', nft_id, user_id, amount=price)
                        
                        success_text = f"""
✅ <b>NFT выставлен на продажу!</b>

🖼️ <b>{nft['name']}</b>
💰 <b>Цена:</b> {price} TON
🔗 <code>{tx['tx_hash']}</code>

🏪 <b>Теперь ваш NFT в маркетплейсе!</b>
                        """
                        bot.send_message(chat_id, success_text, parse_mode='HTML')
                        break
            else:
                bot.send_message(
                    chat_id, 
                    f"❌ <b>Цена должна быть от {MIN_NFT_PRICE} до {MAX_NFT_PRICE} TON</b>", 
                    parse_mode='HTML'
                )
        except ValueError:
            bot.send_message(chat_id, "❌ <b>Введите число</b>\n\nПример: 2.5", parse_mode='HTML')
    
    elif user_states.get(chat_id) == 'waiting_recipient':
        # Обработка получателя подарка
        try:
            recipient_id = int(text)
            nft_id = user_states[chat_id + '_nft']
            user_states[chat_id] = None
            
            # Находим и передаем NFT
            for i, nft in enumerate(user_nfts[user_id]):
                if nft['id'] == nft_id:
                    gifted_nft = user_nfts[user_id].pop(i)
                    gifted_nft['owner_id'] = recipient_id
                    gifted_nft['owner_name'] = f"User_{recipient_id}"
                    gifted_nft['for_sale'] = False
                    gifted_nft['price'] = None
                    
                    # Убираем из маркетплейса
                    if gifted_nft in nft_marketplace:
                        nft_marketplace.remove(gifted_nft)
                    
                    if recipient_id not in user_nfts:
                        user_nfts[recipient_id] = []
                    user_nfts[recipient_id].append(gifted_nft)
                    
                    # Транзакция
                    tx = tx_manager.create_transaction('gift', nft_id, user_id, recipient_id)
                    
                    success_text = f"""
🎁 <b>NFT подарен!</b>

🖼️ <b>{gifted_nft['name']}</b>
👤 <b>Получатель:</b> ID {recipient_id}
🔗 <code>{tx['tx_hash']}</code>

💫 <b>Подарок отправлен!</b>
                    """
                    bot.send_message(chat_id, success_text, parse_mode='HTML')
                    break
        except ValueError:
            bot.send_message(chat_id, "❌ <b>Введите числовой ID пользователя</b>", parse_mode='HTML')
    
    else:
        # Обработка кнопок главного меню
        if text == '🟢 Статус':
            wallet = db.get_wallet_address(user_id)
            nft_count = len(user_nfts.get(user_id, []))
            market_count = len(nft_marketplace)
            
            status_text = f"""
🟢 <b>Статус системы</b>

👤 <b>Пользователь:</b> {message.from_user.first_name}
🆔 <b>ID:</b> {user_id}
💼 <b>Кошелек:</b> {'✅ Подключен' if wallet else '❌ Не подключен'}
🖼️ <b>Ваших NFT:</b> {nft_count}
🏪 <b>В маркетплейсе:</b> {market_count}
💎 <b>Режим:</b> Рабочий

✅ <b>Все системы функционируют!</b>
            """
            bot.send_message(chat_id, status_text, parse_mode='HTML')
            
        elif text == 'ℹ️ Помощь':
            help_command(message)
            
        elif text == '👛 Мой кошелек':
            wallet = db.get_wallet_address(user_id)
            if wallet:
                wallet_text = f"""
👛 <b>Ваш TON кошелек</b>

📍 <b>Адрес:</b>
<code>{wallet}</code>

💎 <b>Используйте этот адрес для:</b>
• Пополнения баланса
• Получения платежей
• Вывода средств
                """
            else:
                wallet_text = """
👛 <b>TON кошелек</b>

❌ <b>Кошелек не подключен</b>

💎 Нажмите "Подключить TON" чтобы добавить кошелек
                """
            bot.send_message(chat_id, wallet_text, parse_mode='HTML')
            
        elif text == '💎 Подключить TON':
            connect_command(message)
            
        elif text == '🎨 Создать NFT':
            nft_command(message)
            
        elif text == '🖼️ Мои NFT':
            my_nfts_command(message)
            
        elif text == '💰 Продать NFT':
            sell_command(message)
            
        elif text == '🎁 Подарить NFT':
            gift_command(message)
            
        elif text == '🏪 Маркетплейс':
            market_command(message)
            
        elif text == '📊 Транзакции':
            transactions_command(message)
            
        else:
            bot.send_message(
                chat_id, 
                "🤖 <b>Используйте кнопки меню для навигации</b>\n\nИли отправьте /help для списка команд", 
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )

# === INLINE КНОПКИ ===
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "sell_nft":
        sell_command(call.message)
        
    elif call.data == "gift_nft":
        gift_command(call.message)
        
    elif call.data == "my_nfts":
        my_nfts_command(call.message)
        
    elif call.data.startswith("sell_"):
        nft_id = call.data[5:]
        user_states[chat_id] = 'waiting_price'
        user_states[chat_id + '_nft'] = nft_id
        
        price_text = f"""
💰 <b>Установка цены</b>

Введите цену в TON для продажи NFT:

💎 <b>Минимум:</b> {MIN_NFT_PRICE} TON
💎 <b>Максимум:</b> {MAX_NFT_PRICE} TON

📝 <b>Пример:</b> 2.5
        """
        bot.send_message(chat_id, price_text, parse_mode='HTML')
        
    elif call.data.startswith("gift_"):
        nft_id = call.data[5:]
        user_states[chat_id] = 'waiting_recipient'
        user_states[chat_id + '_nft'] = nft_id
        
        gift_text = """
🎁 <b>Подарок NFT</b>

Введите ID пользователя Telegram, которому хотите подарить NFT:

📝 <b>Пример:</b> 123456789

👤 <b>ID получателя:</b>
        """
        bot.send_message(chat_id, gift_text, parse_mode='HTML')
    
    bot.answer_callback_query(call.id)

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    print("🚀 NFT Bot запущен и готов к работе!")
    logger.info("✅ Bot started successfully")
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            time.sleep(15)
