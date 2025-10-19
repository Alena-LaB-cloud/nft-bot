import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '788630583').split(',')]
MIN_NFT_PRICE = 0.1
MAX_NFT_PRICE = 100.0
TON_NETWORK = 'testnet'

BOT_TOKEN = os.getenv('BOT_TOKEN', '8429039115:AAFLkJFjhgbpMyva7Kf5fHydDOVIPWdRCdc')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '788630583').split(',')]
MIN_NFT_PRICE = 0.1
MAX_NFT_PRICE = 100.0
TON_NETWORK = 'testnet'
