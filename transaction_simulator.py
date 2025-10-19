import time
import random
from datetime import datetime


class TransactionSimulator:
    """Симулятор TON транзакций для демонстрации"""

    def __init__(self):
        self.transactions = {}

    def simulate_sale(self, nft_id: str, seller_id: int, buyer_id: int, price: float) -> dict:
        """Симуляция продажи NFT"""
        tx_hash = f"tx_{int(time.time())}_{random.randint(1000, 9999)}"

        transaction = {
            'tx_hash': tx_hash,
            'nft_id': nft_id,
            'from_user': seller_id,
            'to_user': buyer_id,
            'amount': price,
            'type': 'sale',
            'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999),
            'fee': round(price * 0.05, 4)  # комиссия 5%
        }

        self.transactions[tx_hash] = transaction
        return transaction

    def simulate_gift(self, nft_id: str, from_user: int, to_user: int) -> dict:
        """Симуляция дарения NFT"""
        tx_hash = f"gift_{int(time.time())}_{random.randint(1000, 9999)}"

        transaction = {
            'tx_hash': tx_hash,
            'nft_id': nft_id,
            'from_user': from_user,
            'to_user': to_user,
            'amount': 0.0,
            'type': 'gift',
            'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999),
            'fee': 0.01  # минимальная комиссия
        }

        self.transactions[tx_hash] = transaction
        return transaction

    def simulate_mint(self, nft_id: str, user_id: int) -> dict:
        """Симуляция создания (минта) NFT"""
        tx_hash = f"mint_{int(time.time())}_{random.randint(1000, 9999)}"

        transaction = {
            'tx_hash': tx_hash,
            'nft_id': nft_id,
            'from_user': None,  # минт из ниоткуда
            'to_user': user_id,
            'amount': 0.0,
            'type': 'mint',
            'status': 'completed',
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            'block': random.randint(1000000, 9999999),
            'fee': 0.05
        }

        self.transactions[tx_hash] = transaction
        return transaction

    def get_transaction_info(self, tx_hash: str) -> dict:
        """Получить информацию о транзакции"""
        return self.transactions.get(tx_hash, {})

    def get_user_transactions(self, user_id: int) -> list:
        """Получить все транзакции пользователя"""
        user_txs = []
        for tx in self.transactions.values():
            if tx['from_user'] == user_id or tx['to_user'] == user_id:
                user_txs.append(tx)
        return user_txs


# Синглтон симулятора
tx_simulator = TransactionSimulator()
