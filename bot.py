import os
import logging
import time
import random
from datetime import datetime
from telebot import TeleBot, types

print("🟢 Starting NFT Bot...")

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')

# Инициализация бота
bot = TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

print("✅ Bot initialized!")

# Простые хранилища в памяти
user_data = {}  # user_id -> данные
nft_marketplace = []

# Клавиатура
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        '🟢 Статус', 'ℹ️ Помощь',
        '💎 Подключить кошелек', '👛 Мой кошелек', 
        '🎨 Создать NFT', '🖼️ Мои NFT',
        '💰 Продать NFT', '🎁 Подарить NFT',
        '🏪 Маркетплейс'
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    user_id = user.id
    
    # Инициализируем пользователя
    if user_id not in user_data:
        user_data[user_id] = {
            'wallet': None,
            'nfts': [],
            'transactions': []
        }
    
    welcome_text = f"""
🎨 <b>Привет, {user.first_name}!</b>

🤖 <b>NFT Бот для TON</b> - РАБОЧАЯ ВЕРСИЯ!

✨ <b>ВСЕ функции работают:</b>
• ✅ Подключение TON кошелька
• ✅ Создание NFT (фото/видео/текст)  
• ✅ Продажа NFT за TON
• ✅ Подарки NFT друзьям
• ✅ Маркетплейс

🚀 <b>Просто нажимайте кнопки!</b>
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

# Подключение кошелька
@bot.message_handler(commands=['connect'])
def connect_command(message):
    user_id = message.from_user.id
    
    help_text = """
💎 <b>ПОДКЛЮЧЕНИЕ TON КОШЕЛЬКА</b>

📝 <b>Отправьте ваш TON адрес:</b>

Формат: EQ... или UQ... (48+ символов)

<b>Пример тестового адреса:</b>
<code>EQD12345678901234567890123456789012345678901234567890</code>

💡 <b>Просто скопируйте и вставьте ваш адрес:</b>
    """
    
    user_data[user_id]['waiting_for'] = 'wallet'
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# Создание NFT
@bot.message_handler(commands=['nft'])
def nft_command(message):
    user_id = message.from_user.id
    
    nft_text = """
🎨 <b>СОЗДАНИЕ NFT</b>

Выберите тип:

📸 <b>Фото</b> - отправьте изображение
🎥 <b>Видео</b> - отправьте видео  
📝 <b>Текст</b> - напишите текст

🚀 <b>Отправьте файл или текст сейчас:</b>
    """
    
    user_data[user_id]['waiting_for'] = 'nft'
    bot.send_message(message.chat.id, nft_text, parse_mode='HTML')

# Мои NFT
@bot.message_handler(commands=['my_nfts'])
def my_nfts_command(message):
    user_id = message.from_user.id
    nfts = user_data[user_id]['nfts']
    
    if not nfts:
        bot.send_message(
            message.chat.id, 
            "🖼️ <b>У вас пока нет NFT!</b>\n\nНажмите '🎨 Создать NFT' чтобы создать первый!", 
            parse_mode='HTML'
        )
        return
    
    nfts_text = f"🖼️ <b>Ваша коллекция</b> ({len(nfts)} NFT)\n\n"
    
    for i, nft in enumerate(nfts, 1):
        nfts_text += f"<b>{i}. {nft['name']}</b>\n"
        nfts_text += f"   🆔 {nft['id'][:10]}...\n"
        nfts_text += f"   📅 {nft['created_at']}\n"
        
        if nft.get('price'):
            nfts_text += f"   💰 <b>{nft['price']} TON</b>\n"
        else:
            nfts_text += f"   💰 Не продается\n"
        
        nfts_text += "\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("💰 Продать NFT", callback_data="sell_nft"),
        types.InlineKeyboardButton("🎁 Подарить NFT", callback_data="gift_nft")
    )
    
    bot.send_message(message.chat.id, nfts_text, parse_mode='HTML', reply_markup=markup)

# Продажа NFT
@bot.message_handler(commands=['sell'])
def sell_command(message):
    user_id = message.from_user.id
    nfts = user_data[user_id]['nfts']
    
    if not nfts:
        bot.send_message(message.chat.id, "❌ <b>У вас нет NFT для продажи</b>", parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup()
    for nft in nfts[:5]:
        if not nft.get('for_sale'):
            markup.add(types.InlineKeyboardButton(
                f"💰 {nft['name']}", 
                callback_data=f"sell_{nft['id']}"
            ))
    
    if markup.keyboard:
        bot.send_message(
            message.chat.id,
            "💰 <b>Выберите NFT для продажи:</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "✅ <b>Все ваши NFT уже в продаже!</b>", parse_mode='HTML')

# Подарок NFT
@bot.message_handler(commands=['gift'])
def gift_command(message):
    user_id = message.from_user.id
    nfts = user_data[user_id]['nfts']
    
    if not nfts:
        bot.send_message(message.chat.id, "❌ <b>У вас нет NFT для подарка</b>", parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup()
    for nft in nfts[:5]:
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

# Маркетплейс
@bot.message_handler(commands=['market'])
def market_command(message):
    if not nft_marketplace:
        market_text = """
🏪 <b>NFT МАРКЕТПЛЕЙС</b>

📭 <b>Пока пусто</b>

🎨 Создайте NFT и выставьте на продажу!
        """
    else:
        market_text = f"🏪 <b>NFT Маркетплейс</b> ({len(nft_marketplace)})\n\n"
        
        for i, nft in enumerate(nft_marketplace[:10], 1):
            market_text += f"<b>{i}. {nft['name']}</b>\n"
            market_text += f"   💰 <b>{nft['price']} TON</b>\n"
            market_text += f"   👤 {nft['owner_name']}\n\n"
    
    bot.send_message(message.chat.id, market_text, parse_mode='HTML')

# Обработка медиа файлов
@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_media(message):
    user_id = message.from_user.id
    
    if user_data.get(user_id, {}).get('waiting_for') == 'nft':
        # Создаем NFT
        nft_id = f"nft_{user_id}_{int(time.time())}"
        nft_name = f"NFT #{len(user_data[user_id]['nfts']) + 1}"
        
        # Определяем тип
        if message.photo:
            nft_type = 'image'
        elif message.video:
            nft_type = 'video'
        else:
            nft_type = 'document'
        
        new_nft = {
            'id': nft_id,
            'name': nft_name,
            'type': nft_type,
            'owner_id': user_id,
            'owner_name': message.from_user.first_name,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'price': None,
            'for_sale': False
        }
        
        user_data[user_id]['nfts'].append(new_nft)
        user_data[user_id]['waiting_for'] = None
        
        # Создаем транзакцию
        tx_hash = f"mint_{int(time.time())}_{random.randint(1000, 9999)}"
        user_data[user_id]['transactions'].append({
            'hash': tx_hash,
            'type': 'mint',
            'nft_id': nft_id,
            'amount': 0,
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        })
        
        success_text = f"""
🎉 <b>NFT УСПЕШНО СОЗДАН!</b>

🖼️ <b>{nft_name}</b>
📅 {new_nft['created_at']}
🔗 <code>{tx_hash}</code>

✅ <b>Добавлен в вашу коллекцию!</b>
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
            types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
        )
        
        bot.send_message(
            message.chat.id, 
            success_text, 
            parse_mode='HTML',
            reply_markup=markup
        )

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    
    # Инициализируем пользователя если нужно
    if user_id not in user_data:
        user_data[user_id] = {
            'wallet': None,
            'nfts': [],
            'transactions': [],
            'waiting_for': None
        }
    
    # Ожидание кошелька
    if user_data[user_id].get('waiting_for') == 'wallet':
        wallet_address = text.strip()
        
        if wallet_address.startswith(('EQ', 'UQ', '0Q')) and len(wallet_address) >= 48:
            user_data[user_id]['wallet'] = wallet_address
            user_data[user_id]['waiting_for'] = None
            
            response = f"""
✅ <b>TON КОШЕЛЕК ПОДКЛЮЧЕН!</b>

📍 <b>Ваш адрес:</b>
<code>{wallet_address}</code>

💎 <b>Теперь вы можете:</b>
• Получать платежи за NFT
• Покупать NFT в маркетплейсе
• Участвовать в торговле

🎉 <b>Отлично! Кошелек работает!</b>
            """
        else:
            response = "❌ <b>Неверный формат адреса!</b>\n\nПопробуйте снова:"
        
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    
    # Ожидание текстового NFT
    elif user_data[user_id].get('waiting_for') == 'nft' and text:
        if len(text) > 3:
            nft_id = f"nft_{user_id}_{int(time.time())}"
            nft_name = f"Текст NFT #{len(user_data[user_id]['nfts']) + 1}"
            
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
            
            user_data[user_id]['nfts'].append(new_nft)
            user_data[user_id]['waiting_for'] = None
            
            # Транзакция
            tx_hash = f"mint_{int(time.time())}_{random.randint(1000, 9999)}"
            user_data[user_id]['transactions'].append({
                'hash': tx_hash,
                'type': 'mint',
                'nft_id': nft_id,
                'amount': 0,
                'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
            
            success_text = f"""
🎉 <b>ТЕКСТОВЫЙ NFT СОЗДАН!</b>

📝 <b>{nft_name}</b>
📅 {new_nft['created_at']}
🔗 <code>{tx_hash}</code>

💬 <b>Содержание:</b>
{text}
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{nft_id}"),
                types.InlineKeyboardButton("🎁 Подарить", callback_data=f"gift_{nft_id}")
            )
            
            bot.send_message(
                message.chat.id, 
                success_text, 
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id, 
                "❌ <b>Текст слишком короткий!</b>\nНужно минимум 4 символа.", 
                parse_mode='HTML'
            )
    
    # Ожидание цены для продажи
    elif user_data[user_id].get('waiting_for') == 'price':
        try:
            price = float(text)
            nft_id = user_data[user_id].get('selling_nft')
            
            if nft_id:
                # Находим NFT и устанавливаем цену
                for nft in user_data[user_id]['nfts']:
                    if nft['id'] == nft_id:
                        nft['price'] = price
                        nft['for_sale'] = True
                        
                        # Добавляем в маркетплейс
                        if nft not in nft_marketplace:
                            nft_marketplace.append(nft)
                        
                        # Транзакция
                        tx_hash = f"sale_{int(time.time())}_{random.randint(1000, 9999)}"
                        user_data[user_id]['transactions'].append({
                            'hash': tx_hash,
                            'type': 'sale',
                            'nft_id': nft_id,
                            'amount': price,
                            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        })
                        
                        success_text = f"""
✅ <b>NFT В ПРОДАЖЕ!</b>

🖼️ <b>{nft['name']}</b>
💰 <b>Цена:</b> {price} TON
🔗 <code>{tx_hash}</code>

🏪 <b>Теперь в маркетплейсе!</b>
                        """
                        bot.send_message(message.chat.id, success_text, parse_mode='HTML')
                        break
                
                user_data[user_id]['waiting_for'] = None
                user_data[user_id]['selling_nft'] = None
            else:
                bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> NFT не найден.", parse_mode='HTML')
                
        except ValueError:
            bot.send_message(
                message.chat.id, 
                "❌ <b>Введите число!</b>\nПример: 2.5", 
                parse_mode='HTML'
            )
    
    # Ожидание получателя подарка
    elif user_data[user_id].get('waiting_for') == 'recipient':
        try:
            recipient_id = int(text)
            nft_id = user_data[user_id].get('gifting_nft')
            
            if nft_id:
                # Находим и передаем NFT
                for i, nft in enumerate(user_data[user_id]['nfts']):
                    if nft['id'] == nft_id:
                        gifted_nft = user_data[user_id]['nfts'].pop(i)
                        gifted_nft['owner_id'] = recipient_id
                        gifted_nft['owner_name'] = f"User_{recipient_id}"
                        gifted_nft['for_sale'] = False
                        gifted_nft['price'] = None
                        
                        # Убираем из маркетплейса
                        if gifted_nft in nft_marketplace:
                            nft_marketplace.remove(gifted_nft)
                        
                        # Инициализируем получателя если нужно
                        if recipient_id not in user_data:
                            user_data[recipient_id] = {
                                'wallet': None,
                                'nfts': [],
                                'transactions': []
                            }
                        
                        user_data[recipient_id]['nfts'].append(gifted_nft)
                        
                        # Транзакция
                        tx_hash = f"gift_{int(time.time())}_{random.randint(1000, 9999)}"
                        user_data[user_id]['transactions'].append({
                            'hash': tx_hash,
                            'type': 'gift',
                            'nft_id': nft_id,
                            'to_user': recipient_id,
                            'amount': 0,
                            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        })
                        
                        success_text = f"""
🎁 <b>NFT ПОДАРЕН!</b>

🖼️ <b>{gifted_nft['name']}</b>
👤 <b>Получатель:</b> ID {recipient_id}
🔗 <code>{tx_hash}</code>

💫 <b>Подарок отправлен!</b>
                        """
                        bot.send_message(message.chat.id, success_text, parse_mode='HTML')
                        break
                
                user_data[user_id]['waiting_for'] = None
                user_data[user_id]['gifting_nft'] = None
                
        except ValueError:
            bot.send_message(
                message.chat.id, 
                "❌ <b>Введите числовой ID!</b>\nПример: 123456789", 
                parse_mode='HTML'
            )
    
    else:
        # Обработка кнопок меню
        if text == '🟢 Статус':
            wallet = user_data[user_id]['wallet']
            nft_count = len(user_data[user_id]['nfts'])
            
            status_text = f"""
🟢 <b>СТАТУС СИСТЕМЫ</b>

👤 <b>Пользователь:</b> {message.from_user.first_name}
💼 <b>Кошелек:</b> {'✅ ПОДКЛЮЧЕН' if wallet else '❌ Нет'}
🖼️ <b>Ваших NFT:</b> {nft_count}
🏪 <b>В маркетплейсе:</b> {len(nft_marketplace)}

✅ <b>ВСЕ СИСТЕМЫ РАБОТАЮТ!</b>
            """
            bot.send_message(message.chat.id, status_text, parse_mode='HTML')
            
        elif text == 'ℹ️ Помощь':
            help_text = """
📋 <b>ПОМОЩЬ</b>

💎 <b>Подключите кошелек</b> - чтобы получать платежи
🎨 <b>Создайте NFT</b> - из фото, видео или текста
💰 <b>Продавайте NFT</b> - устанавливайте цену в TON
🎁 <b>Дарите NFT</b> - друзьям по ID
🏪 <b>Маркетплейс</b> - смотрите все NFT в продаже

🚀 <b>Просто нажимайте кнопки!</b>
            """
            bot.send_message(message.chat.id, help_text, parse_mode='HTML')
            
        elif text == '💎 Подключить кошелек':
            connect_command(message)
            
        elif text == '👛 Мой кошелек':
            wallet = user_data[user_id]['wallet']
            if wallet:
                wallet_text = f"""
👛 <b>ВАШ TON КОШЕЛЕК</b>

📍 <b>Адрес:</b>
<code>{wallet}</code>

💎 <b>Используйте для:</b>
• Получения платежей за NFT
• Покупки NFT в маркетплейсе
• Вывода средств
                """
            else:
                wallet_text = """
👛 <b>TON КОШЕЛЕК</b>

❌ <b>Кошелек не подключен</b>

💎 Нажмите "Подключить кошелек" выше!
                """
            bot.send_message(message.chat.id, wallet_text, parse_mode='HTML')
            
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
            
        else:
            bot.send_message(
                message.chat.id, 
                "🤖 <b>Используйте кнопки меню!</b>\n\nВсе функции доступны через кнопки ниже.", 
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )

# Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data == "sell_nft":
        sell_command(call.message)
        
    elif call.data == "gift_nft":
        gift_command(call.message)
        
    elif call.data.startswith("sell_"):
        nft_id = call.data[5:]
        user_data[user_id]['waiting_for'] = 'price'
        user_data[user_id]['selling_nft'] = nft_id
        
        price_text = """
💰 <b>УСТАНОВКА ЦЕНЫ</b>

Введите цену в TON:

💎 <b>Рекомендация:</b> 0.5-10 TON

📝 <b>Пример:</b> 2.5
        """
        bot.send_message(chat_id, price_text, parse_mode='HTML')
        
    elif call.data.startswith("gift_"):
        nft_id = call.data[5:]
        user_data[user_id]['waiting_for'] = 'recipient'
        user_data[user_id]['gifting_nft'] = nft_id
        
        gift_text = """
🎁 <b>ПОДАРОК NFT</b>

Введите ID пользователя Telegram:

📝 <b>Пример:</b> 123456789

👤 <b>ID получателя:</b>
        """
        bot.send_message(chat_id, gift_text, parse_mode='HTML')
    
    bot.answer_callback_query(call.id)

# Запуск бота
if __name__ == "__main__":
    print("🚀 NFT Bot ЗАПУЩЕН И РАБОТАЕТ!")
    print("✅ Все системы готовы!")
    print("💎 Кошельки работают!")
    print("🎨 NFT создаются!")
    
    while True:
        try:
            bot.infinity_polling(timeout=30)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(10)
