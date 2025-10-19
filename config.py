import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '788630583').split(',')]

# Настройки TON
TON_NETWORK = os.getenv('TON_NETWORK')
TON_API_KEY = os.getenv('TON_API_KEY')

# Настройки ценообразования
MIN_NFT_PRICE = float(os.getenv('MIN_NFT_PRICE', '0.1'))
MAX_NFT_PRICE = float(os.getenv('MAX_NFT_PRICE', '1000.0'))
CREATION_FEE = float(os.getenv('CREATION_FEE', '0.1'))

# Настройки файлов
BASE_DIR = os.getenv('BASE_DIR', 'users_data')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
