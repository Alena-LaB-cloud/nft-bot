import time
import random
from datetime import datetime

class TransactionManager:
    def __init__(self):
        self.transactions = {}
    
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

# Глобальный менеджер транзакций
tx_manager = TransactionManager()
