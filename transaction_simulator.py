import time
import random
from datetime import datetime

class TransactionSimulator:
    def __init__(self):
        self.transactions = {}
    
    def simulate_sale(self, nft_id: str, seller_id: int, price: float) -> dict:
        tx_hash = f"tx_{int(time.time())}_{random.randint(1000, 9999)}"
        transaction = {
            'tx_hash': tx_hash, 'nft_id': nft_id, 'from_user': seller_id,
            'amount': price, 'type': 'sale', 'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999), 'fee': round(price * 0.05, 4)
        }
        self.transactions[tx_hash] = transaction
        return transaction
    
    def simulate_gift(self, nft_id: str, from_user: int, to_user: int) -> dict:
        tx_hash = f"gift_{int(time.time())}_{random.randint(1000, 9999)}"
        transaction = {
            'tx_hash': tx_hash, 'nft_id': nft_id, 'from_user': from_user, 'to_user': to_user,
            'amount': 0.0, 'type': 'gift', 'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999), 'fee': 0.01
        }
        self.transactions[tx_hash] = transaction
        return transaction
    
    def simulate_mint(self, nft_id: str, user_id: int) -> dict:
        tx_hash = f"mint_{int(time.time())}_{random.randint(1000, 9999)}"
        transaction = {
            'tx_hash': tx_hash, 'nft_id': nft_id, 'to_user': user_id,
            'amount': 0.0, 'type': 'mint', 'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999), 'fee': 0.05
        }
        self.transactions[tx_hash] = transaction
        return transaction
    
    def get_user_transactions(self, user_id: int) -> list:
        return [tx for tx in self.transactions.values() 
                if tx.get('from_user') == user_id or tx.get('to_user') == user_id]

tx_simulator = TransactionSimulator()


# Синглтон симулятора
tx_simulator = TransactionSimulator()

