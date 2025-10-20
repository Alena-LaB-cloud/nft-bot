import asyncio
import requests
import logging
from typing import Dict
from pytoniq import LiteBalancer, Address

logger = logging.getLogger(__name__)


class TONManager:
    """Менеджер для работы с TON блокчейном"""

    def __init__(self, network: str = "testnet"):
        self.network = network
        self.provider = None
        self.tonapi_url = "https://testnet.tonapi.io/v2" if network == "testnet" else "https://tonapi.io/v2"

    async def init_provider(self):
        """Инициализация провайдера TON"""
        try:
            if self.network == "testnet":
                self.provider = LiteBalancer.from_testnet_config(trust_level=1)
            else:
                self.provider = LiteBalancer.from_mainnet_config(trust_level=1)

            await self.provider.start_up()
            logger.info(f"✅ TON provider initialized for {self.network}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize TON provider: {e}")
            return False

    async def close_provider(self):
        """Закрытие провайдера"""
        if self.provider:
            await self.provider.close_all()

    def validate_wallet_address(self, address: str) -> bool:
        """Проверка валидности TON адреса"""
        try:
            addr = Address(address)
            return True
        except Exception as e:
            logger.error(f"Invalid address {address}: {e}")
            return False

    async def get_wallet_balance(self, wallet_address: str) -> float:
        """Получение баланса кошелька в TON"""
        try:
            if not self.provider:
                success = await self.init_provider()
                if not success:
                    return await self._get_balance_from_api(wallet_address)

            address = Address(wallet_address)
            balance = await self.provider.get_balance(address)
            return balance / 1e9  # Конвертируем наноTON в TON
        except Exception as e:
            logger.error(f"Error getting wallet balance from provider: {e}")
            return await self._get_balance_from_api(wallet_address)

    async def _get_balance_from_api(self, wallet_address: str) -> float:
        """Получение баланса через TON API"""
        try:
            url = f"{self.tonapi_url}/accounts/{wallet_address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance = int(data.get('balance', 0)) / 1e9
                return balance
            return 0.0
        except Exception as e:
            logger.error(f"Error getting wallet balance from API: {e}")
            return 0.0

    def get_ton_price(self) -> float:
        """Получение текущей цены TON в USD"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data['the-open-network']['usd']
            return 2.5  # fallback цена
        except Exception as e:
            logger.error(f"Error getting TON price: {e}")
            return 2.5

    def convert_ton_to_usd(self, ton_amount: float) -> float:
        """Конвертирует TON в USD"""
        ton_price = self.get_ton_price()
        return ton_amount * ton_price

    async def get_wallet_info(self, wallet_address: str) -> Dict:
        """Получает полную информацию о кошельке"""
        balance = await self.get_wallet_balance(wallet_address)

        return {
            "address": wallet_address,
            "balance_ton": balance,
            "balance_usd": self.convert_ton_to_usd(balance),
            "network": self.network,
            "is_active": balance > 0
        }

    async def create_nft_transaction(self, owner_address: str, metadata_uri: str, amount: float = 0.05) -> Dict:
        """Создает транзакцию для минта NFT"""
        try:
            # В реальном приложении здесь будет создание реальной транзакции
            # Пока возвращаем симуляцию
            return {
                "success": True,
                "transaction_hash": f"fake_tx_{int(asyncio.get_event_loop().time())}",
                "nft_address": f"EQD{owner_address[2:]}",
                "amount": amount,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error creating NFT transaction: {e}")
            return {"success": False, "error": str(e)}


# Синглтон менеджер
ton_manager = TONManager()
