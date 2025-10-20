import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '1222144963').split(',')]

# Настройки TON
TON_NETWORK = os.getenv('TON_NETWORK', 'testnet')
TON_API_KEY = os.getenv('TON_API_KEY', '')
TONCENTER_API_KEY = os.getenv('TONCENTER_API_KEY', '')

# Настройки NFT
NFT_COLLECTION_ADDRESS = os.getenv('NFT_COLLECTION_ADDRESS', '')
MIN_NFT_PRICE = float(os.getenv('MIN_NFT_PRICE', '0.1'))
MAX_NFT_PRICE = float(os.getenv('MAX_NFT_PRICE', '1000.0'))

# Настройки безопасности
REQUIRE_TON_PROOF = os.getenv('REQUIRE_TON_PROOF', 'true').lower() == 'true'
