import os
import asyncio
from dbm import sqlite3

from telebot import TeleBot, types
from telebot.types import Message, CallbackQuery
import tempfile
import logging
from config import ADMIN_IDS, MIN_NFT_PRICE, MAX_NFT_PRICE
from ton_connector import TonConnect
from ton_manager import ton_manager
from nft_creator import NFTCreator
from DataBase import init_database, save_wallet_address, get_wallet_address


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = TeleBot('8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
nft_creator = NFTCreator()

# Состояния пользователей
user_states = {}


class UserState:
    """Класс для управления состоянием пользователя"""

    def __init__(self):
        self.waiting_for = None
        self.data = {}

    def set_state(self, state: str, data: dict = None):
        self.waiting_for = state
        if data:
            self.data.update(data)

    def clear_state(self):
        self.waiting_for = None
        self.data = {}


def get_user_state(user_id: int) -> UserState:
    if user_id not in user_states:
        user_states[user_id] = UserState()
    return user_states[user_id]


# Команды бота
@bot.message_handler(commands=['start'])
def start_command(message: Message):
    """Команда /start"""
    user = message.from_user

    welcome_text = f"""
🎨 Привет, {user.first_name}!

Я помогу тебе создавать NFT в сети TON!

✨ Что я умею:
• Создавать NFT из твоих фото
• Выставлять NFT на продажу за TON
• Передавать NFT другим пользователям
• Показывать баланс TON кошелька

💎 Основные команды:
/connect - Подключить TON кошелек
/balance - Проверить баланс
/create - Создать NFT из фото
/my_nfts - Мои NFT
/marketplace - Маркетплейс NFT
/sell - Продать NFT
/gift - Подарить NFT

💰 Создание NFT абсолютно бесплатно!
    """

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('💎 Подключить кошелек')
    btn2 = types.KeyboardButton('💰 Баланс')
    btn3 = types.KeyboardButton('🎨 Создать NFT')
    btn4 = types.KeyboardButton('📦 Мои NFT')
    btn5 = types.KeyboardButton('🏪 Маркетплейс')
    markup.add(btn1, btn2, btn3, btn4, btn5)

    button_text_to_command = {
        '💎 Подключить кошелек': '/connect',
        '💰 Баланс': '/balance',
        '🎨 Создать NFT': '/create',
        '📦 Мои NFT': '/my_nfts',
        '🏪 Маркетплейс': '/marketplace'
    }
        
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.message_handler(commands=['connect'])
def connect_wallet_command(message: Message):
    """Подключение TON кошелька"""
    help_text = """
💎 Подключение TON кошелька:

Отправь мне адрес своего TON кошелька.

📱 Примеры валидных адресов:
• EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c
• UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c

📋 Как найти адрес кошелька:
• @wallet: Нажми "Receive" → "Copy Address"
• Tonkeeper: Нажми на QR-код на главном экране
        
От  правь свой TON адрес:
     """

    bot.send_message(message.chat.id, help_text)
    get_user_state(message.from_user.id).set_state("waiting_wallet")


@bot.message_handler(commands=['connect_wallet'])
def connect_wallet_new(message: Message):
    """Новое подключение кошелька через TonConnect"""
    ton_connector = TonConnect()
    qr_path = ton_connector.generate_connect_qr(message.from_user.id)

    with open(qr_path, 'rb') as qr_photo:
        bot.send_photo(
            message.chat.id,
            qr_photo,
            caption="📱 Отсканируй QR код в своем TON кошельке для подключения\n\n"
                    "Поддерживаемые кошельки:\n"
                    "• Tonkeeper\n• Tonhub\n• MyTonWallet\n• OpenMask"
        )


    if os.path.exists(qr_path):
        os.remove(qr_path)



@bot.message_handler(commands=['mint_nft'])
def mint_nft_blockchain(message: Message):
    """Минт NFT в блокчейн"""
    user_state = get_user_state(message.from_user.id)

    if not user_state.data.get('wallet_connected'):
        bot.send_message(message.chat.id, "❌ Сначала подключи кошелек через /connect_wallet")
        return

    # Логика минта в блокчейн
    bot.send_message(message.chat.id, "🔄 Минт NFT в блокчейн TON...")


@bot.message_handler(commands=['balance'])
def balance_command(message: Message):
    """Проверка баланса"""
    user_id = message.from_user.id

    # Проверяем в БД
    wallet_address = get_wallet_address(user_id)

    if not wallet_address:
        bot.send_message(message.chat.id, "❌ Сначала подключи TON кошелек командой /connect")
        return

    # Используем адрес из БД
    try:
        async def get_balance():
            return await ton_manager.get_wallet_info(wallet_address)

        wallet_info = asyncio.run(get_balance())

        balance_text = f"""
💎 Информация о кошельке:

🏦 Адрес: `{wallet_info['address']}`
💰 Баланс: {wallet_info['balance_ton']:.2f} TON
💵 В долларах: ${wallet_info['balance_usd']:.2f}
🌐 Сеть: {wallet_info['network']}

💫 Статус: {"🟢 Активен" if wallet_info['is_active'] else "🟡 Неактивен"}
        """

        bot.send_message(message.chat.id, balance_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении баланса")

@bot.message_handler(commands=['create'])
def create_nft_command(message: Message):
    """Создание NFT"""
    user_id = message.from_user.id

    # Проверяем в БД, а не в состоянии
    wallet_address = get_wallet_address(user_id)

    if not wallet_address:
        bot.send_message(message.chat.id, "❌ Сначала подключи TON кошелек командой /connect")
        return

    # Сохраняем адрес в состоянии для дальнейшего использования
    user_state = get_user_state(user_id)
    user_state.data['wallet_address'] = wallet_address

    bot.send_message(
        message.chat.id,
        "🎨 Отправь мне фото для создания NFT!\n\n"
        "После отправки фото я помогу:\n"
        "1. Дать название NFT\n"
        "2. Добавить описание\n"
        "3. Установить цену (опционально)\n"
        "4. Создать NFT в блокчейне TON"
    )

    user_state.set_state("waiting_photo")

@bot.message_handler(commands=['my_nfts'])
def my_nfts_command(message: Message):
    """Показать мои NFT"""
    user_id = message.from_user.id
    nfts = nft_creator.get_user_nfts(user_id)

    if not nfts:
        bot.send_message(message.chat.id, "📦 У тебя еще нет NFT. Используй /create чтобы создать первый!")
        return

    # Создаем инлайн-клавиатуру для просмотра NFT
    markup = types.InlineKeyboardMarkup()

    for nft in nfts[:5]:  # Показываем первые 5 NFT
        btn_text = f"🎨 {nft['name']}"
        if nft.get('for_sale'):
            btn_text += f" 💰{nft['price_ton']} TON"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_nft_{nft['id']}"))

    total_value = sum(nft.get('price_ton', 0) for nft in nfts if nft.get('for_sale'))

    bot.send_message(
        message.chat.id,
        f"📦 Твои NFT ({len(nfts)} шт.):\n"
        f"💰 Общая стоимость на продаже: {total_value:.2f} TON\n"
        f"Выбери NFT для просмотра:",
        reply_markup=markup
    )


@bot.message_handler(commands=['marketplace'])
def marketplace_command(message: Message):
    """Маркетплейс NFT"""
    # Здесь будет логика для отображения маркетплейса
    # Пока заглушка
    bot.send_message(
        message.chat.id,
        "🏪 Маркетплейс NFT в разработке...\n\n"
        "Скоро ты сможешь покупать и продавать NFT других пользователей!"
    )


@bot.message_handler(commands=['sell'])
def sell_nft_command(message: Message):
    """Продажа NFT"""
    user_id = message.from_user.id
    nfts = nft_creator.get_user_nfts(user_id)

    # Фильтруем NFT, которые еще не на продаже
    nfts_for_sale = [nft for nft in nfts if not nft.get('for_sale', False)]

    if not nfts_for_sale:
        bot.send_message(message.chat.id, "❌ У тебя нет NFT для продажи или все уже выставлены.")
        return

    markup = types.InlineKeyboardMarkup()
    for nft in nfts_for_sale[:5]:
        markup.add(types.InlineKeyboardButton(f"🎨 {nft['name']}", callback_data=f"sell_{nft['id']}"))

    bot.send_message(message.chat.id, "Выбери NFT для продажи:", reply_markup=markup)


@bot.message_handler(commands=['gift'])
def gift_nft_command(message: Message):
    """Подарок NFT"""
    user_id = message.from_user.id
    nfts = nft_creator.get_user_nfts(user_id)

    if not nfts:
        bot.send_message(message.chat.id, "❌ У тебя нет NFT для подарка.")
        return

    markup = types.InlineKeyboardMarkup()
    for nft in nfts[:5]:
        if not nft.get('for_sale', False):
            markup.add(types.InlineKeyboardButton(f"🎨 {nft['name']}", callback_data=f"gift_{nft['id']}"))

    if not markup.keyboard:
        bot.send_message(message.chat.id, "❌ Все твои NFT выставлены на продажу. Сними с продажи чтобы подарить.")
        return

    bot.send_message(message.chat.id, "🎁 Выбери NFT для подарка:", reply_markup=markup)


@bot.message_handler(content_types=['photo'])
def handle_photo(message: Message):
    """Обработка фото для создания NFT"""
    user_id = message.from_user.id
    user_state = get_user_state(user_id)

    if user_state.waiting_for != "waiting_photo":
        bot.send_message(message.chat.id, "📸 Отличное фото! Чтобы создать NFT, нажми '🎨 Создать NFT'")
        return

    # Скачиваем фото
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохраняем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(downloaded_file)
        temp_path = temp_file.name

    user_state.set_state("waiting_nft_name", {"photo_path": temp_path})
    bot.send_message(message.chat.id, "📸 Фото получено! Теперь введи название для NFT:")


@bot.message_handler(commands=['debug'])
def debug_command(message: Message):
    """Команда для отладки"""
    user_id = message.from_user.id

    # Проверим состояние в БД
    wallet_address = get_wallet_address(user_id)

    debug_text = f"""
🔧 Отладочная информация:

👤 User ID: {user_id}
💼 Кошелек в БД: {wallet_address or '❌ Не найден'}
📊 Всего пользователей в БД: {_get_users_count()}
    """

    bot.send_message(message.chat.id, debug_text)


def _get_users_count():
    """Получает количество пользователей в БД"""
    try:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return f"Ошибка: {e}"



@bot.message_handler(func=lambda message: True)
def handle_text(message: Message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    text = message.text.strip()

    # Обработка подключения кошелька
    if user_state.waiting_for == "waiting_wallet":
        if ton_manager.validate_wallet_address(text):
            # Сохраняем в БД
            success = save_wallet_address(
                user_id=user_id,
                username=message.from_user.username or f"user_{user_id}",
                wallet_address=text
            )

            if success:
                user_state.data['wallet_address'] = text
                user_state.clear_state()

                # Получаем баланс
                async def get_balance():
                    return await ton_manager.get_wallet_balance(text)

                balance = asyncio.run(get_balance())

                bot.send_message(
                    message.chat.id,
                    f"✅ Кошелек подключен и сохранен в базе данных!\n\n"
                    f"👤 User ID: {user_id}\n"
                    f"🏦 Адрес: `{text}`\n"
                    f"💰 Баланс: {balance:.2f} TON\n\n"
                    f"Теперь ты можешь создавать NFT!",
                    parse_mode='Markdown'
                )
                logger.info(f"💰 Wallet saved to DB for user {user_id}")
            else:
                bot.send_message(
                    message.chat.id,
                    "❌ Ошибка сохранения кошелька. Возможно, этот адрес уже используется."
                )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат TON адреса. Попробуй еще раз:"
            )

    # Обработка названия NFT
    elif user_state.waiting_for == "waiting_nft_name":
        if len(text) < 2 or len(text) > 50:
            bot.send_message(message.chat.id, "❌ Название должно быть от 2 до 50 символов. Попробуй еще раз:")
            return

        user_state.set_state("waiting_nft_description", {"nft_name": text})
        bot.send_message(message.chat.id, "📝 Отлично! Теперь введи описание NFT:")

    # Обработка описания NFT
    elif user_state.waiting_for == "waiting_nft_description":
        if len(text) < 10 or len(text) > 500:
            bot.send_message(message.chat.id, "❌ Описание должно быть от 10 до 500 символов. Попробуй еще раз:")
            return

        user_state.set_state("waiting_nft_price", {"nft_description": text})

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚫 Не для продажи", callback_data="price_0"))
        markup.add(types.InlineKeyboardButton("💎 0.5 TON", callback_data="price_0.5"))
        markup.add(types.InlineKeyboardButton("💎 1 TON", callback_data="price_1"))
        markup.add(types.InlineKeyboardButton("💎 5 TON", callback_data="price_5"))

        bot.send_message(
            message.chat.id,
            "💎 Установи цену для NFT или выбери 'Не для продажи':\n"
            f"Минимальная цена: {MIN_NFT_PRICE} TON\n"
            f"Максимальная цена: {MAX_NFT_PRICE} TON",
            reply_markup=markup
        )

    # Обработка цены NFT (ручной ввод)
    elif user_state.waiting_for == "waiting_nft_price":
        try:
            price = float(text)
            if price < 0:
                bot.send_message(message.chat.id, "❌ Цена не может быть отрицательной. Попробуй еще раз:")
                return
            if price > 0 and price < MIN_NFT_PRICE:
                bot.send_message(message.chat.id, f"❌ Минимальная цена {MIN_NFT_PRICE} TON. Попробуй еще раз:")
                return
            if price > MAX_NFT_PRICE:
                bot.send_message(message.chat.id, f"❌ Максимальная цена {MAX_NFT_PRICE} TON. Попробуй еще раз:")
                return

            _create_nft_final(user_id, user_state, price, message.chat.id)

        except ValueError:
            bot.send_message(message.chat.id, "❌ Введи корректное число. Попробуй еще раз:")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    """Обработка нажатий инлайн-кнопок"""
    user_id = call.from_user.id
    user_state = get_user_state(user_id)

    if call.data.startswith("view_nft_"):
        nft_id = call.data.replace("view_nft_", "")
        nft = nft_creator.get_nft(user_id, nft_id)

        if nft and os.path.exists(nft['image_path']):
            with open(nft['image_path'], 'rb') as photo:
                caption = f"🎨 {nft['name']}\n📝 {nft['description']}\n🆔 {nft['id'][:8]}"
                if nft.get('for_sale'):
                    caption += f"\n💰 Цена: {nft['price_ton']} TON"
                else:
                    caption += "\n💫 Не для продажи"

                bot.send_photo(call.message.chat.id, photo, caption=caption)
        else:
            bot.send_message(call.message.chat.id, "❌ NFT не найден")

    elif call.data.startswith("price_"):
        price_str = call.data.replace("price_", "")
        price = 0.0 if price_str == "0" else float(price_str)
        _create_nft_final(user_id, user_state, price, call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith("sell_"):
        nft_id = call.data.replace("sell_", "")
        user_state.set_state("waiting_sell_price", {"nft_id": nft_id})
        bot.send_message(
            call.message.chat.id,
            f"💎 Введи цену в TON для продажи NFT {nft_id[:8]}...\n"
            f"Минимальная цена: {MIN_NFT_PRICE} TON"
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith("gift_"):
        nft_id = call.data.replace("gift_", "")
        user_state.set_state("waiting_gift_recipient", {"nft_id": nft_id})
        bot.send_message(
            call.message.chat.id,
            f"👤 Введи Telegram ID пользователя, которому хочешь подарить NFT {nft_id[:8]}..."
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)


def _create_nft_final(user_id: int, user_state, price: float, chat_id: int):
    """Финальное создание NFT"""
    try:
        # Создаем NFT
        nft_data = nft_creator.create_nft(
            user_id=user_id,
            image_path=user_state.data['photo_path'],
            name=user_state.data['nft_name'],
            description=user_state.data['nft_description'],
            price_ton=price
        )

        if nft_data:
            # Отправляем готовый NFT
            with open(nft_data['image_path'], 'rb') as photo:
                caption = f"🎉 NFT создан!\n\nНазвание: {nft_data['name']}\nОписание: {nft_data['description']}"

                if price > 0:
                    usd_price = ton_manager.convert_ton_to_usd(price)
                    caption += f"\n💰 Цена: {price} TON (${usd_price:.2f})"
                else:
                    caption += "\n💫 Не для продажи"

                caption += f"\n🆔 ID: {nft_data['id'][:8]}"

                bot.send_photo(chat_id, photo, caption=caption)

            # Очищаем временный файл
            if os.path.exists(user_state.data['photo_path']):
                os.remove(user_state.data['photo_path'])

            user_state.clear_state()

            # Уведомляем админа
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        admin_id,
                        f"🆕 Создан новый NFT!\n"
                        f"Пользователь: {user_id}\n"
                        f"NFT: {nft_data['name']}\n"
                        f"Цена: {price} TON"
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin: {e}")

        else:
            bot.send_message(chat_id, "❌ Ошибка при создании NFT")
            user_state.clear_state()

    except Exception as e:
        logger.error(f"Error in NFT creation: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при создании NFT")
        user_state.clear_state()


# Обработка кнопок клавиатуры
@bot.message_handler(func=lambda message: message.text == '💎 Подключить кошелек')
def connect_button(message: Message):
    connect_wallet_command(message)


@bot.message_handler(func=lambda message: message.text == '💰 Баланс')
def balance_button(message: Message):
    balance_command(message)


@bot.message_handler(func=lambda message: message.text == '🎨 Создать NFT')
def create_nft_button(message: Message):
    create_nft_command(message)


@bot.message_handler(func=lambda message: message.text == '📦 Мои NFT')
def my_nfts_button(message: Message):
    my_nfts_command(message)


@bot.message_handler(func=lambda message: message.text == '🏪 Маркетплейс')
def marketplace_button(message: Message):
    marketplace_command(message)

if __name__ == "__main__":
    # Инициализация базы данных
    init_database()

    logger.info("🤖 Запуск NFT бота для TON...")
    logger.info(f"👑 Администраторы: {ADMIN_IDS}")
    logger.info(f"💎 Сеть TON: {ton_manager.network}")
    logger.info(f"💰 Диапазон цен: {MIN_NFT_PRICE}-{MAX_NFT_PRICE} TON")

    # Инициализация TON провайдера
    asyncio.run(ton_manager.init_provider())

    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота...")
        asyncio.run(ton_manager.close_provider())
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {e}")
        asyncio.run(ton_manager.close_provider())

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(10)

