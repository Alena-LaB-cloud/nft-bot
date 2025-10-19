import os
import json
import uuid
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class NFTCreator:
    """Класс для создания и управления NFT"""

    def __init__(self, base_dir: str = "users_data"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def get_user_dir(self, user_id: int) -> str:
        """Создает папку пользователя если не существует"""
        user_dir = os.path.join(self.base_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(os.path.join(user_dir, "nfts"), exist_ok=True)
        os.makedirs(os.path.join(user_dir, "collections"), exist_ok=True)
        return user_dir

    def create_nft_image(self, image_path: str, name: str, price_ton: float = 0) -> str:
        """Создает изображение NFT с рамкой и текстом"""
        try:
            with Image.open(image_path) as img:
                # Создаем квадратное изображение
                size = min(img.size)
                left = (img.width - size) // 2
                top = (img.height - size) // 2
                cropped = img.crop((left, top, left + size, top + size))

                # Уменьшаем до стандартного размера
                nft_size = (500, 500)
                nft_img = cropped.resize(nft_size, Image.Resampling.LANCZOS)

                # Создаем новое изображение с рамкой
                border_size = 10
                final_size = (nft_size[0] + border_size * 2, nft_size[1] + border_size * 2 + 50)
                final_img = Image.new("RGB", final_size, "black")
                final_img.paste(nft_img, (border_size, border_size))

                # Добавляем текст
                draw = ImageDraw.Draw(final_img)

                try:
                    title_font = ImageFont.truetype("arial.ttf", 20)
                    price_font = ImageFont.truetype("arial.ttf", 16)
                except Exception as e:
                    title_font = ImageFont. load_default()
                    price_font = ImageFont.load_default()

                # Название NFT
                draw.text((border_size + 10, nft_size[1] + border_size + 5),
                          name[:25], fill="white", font=title_font)

                # Цена если есть
                if price_ton > 0:
                    price_text = f"{price_ton} TON"
                    text_width = draw.textlength(price_text, font=price_font)
                    draw.text((final_size[0] - text_width - 10, nft_size[1] + border_size + 10),
                              price_text, fill="gold", font=price_font)

                # Сохраняем результат
                output_path = os.path.join(os.path.dirname(image_path), f"nft_{uuid.uuid4().hex[:8]}.png")
                final_img.save(output_path, "PNG")

                return output_path

        except Exception as e:
            logger.error(f"Error creating NFT image: {e}")
            return image_path  # Возвращаем оригинал в случае ошибки

    def save_nft_metadata(self, user_id: int, nft_data: Dict) -> bool:
        """Сохраняет метаданные NFT"""
        try:
            user_dir = self.get_user_dir(user_id)
            nft_id = nft_data["id"]

            metadata_path = os.path.join(user_dir, "nfts", f"{nft_id}.json")

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(nft_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error saving NFT metadata: {e}")
            return False

    def create_nft(self, user_id: int, image_path: str, name: str,
                   description: str, collection: str = None,
                   price_ton: float = 0) -> Optional[Dict]:
        """Создает новый NFT"""
        try:
            # Создаем уникальный ID
            nft_id = str(uuid.uuid4())

            # Создаем улучшенное изображение
            nft_image_path = self.create_nft_image(image_path, name, price_ton)

            # Метаданные NFT
            nft_data = {
                "id": nft_id,
                "name": name,
                "description": description,
                "collection": collection,
                "owner_id": user_id,
                "price_ton": price_ton,
                "for_sale": price_ton > 0,
                "image_path": nft_image_path,
                "created_at": time.time(),
                "transactions": [],
                "metadata_uri": f"ipfs://{nft_id}",  # В реальном приложении здесь будет IPFS URI
                "external_links": {}
            }

            # Сохраняем метаданные
            if self.save_nft_metadata(user_id, nft_data):
                # Обновляем статистику пользователя
                self._update_user_stats(user_id, nfts_created=1)
                return nft_data

            return None

        except Exception as e:
            logger.error(f"Error creating NFT: {e}")
            return None

    def get_user_nfts(self, user_id: int) -> List[Dict]:
        """Получает все NFT пользователя"""
        nfts = []
        user_dir = self.get_user_dir(user_id)
        nfts_dir = os.path.join(user_dir, "nfts")

        if not os.path.exists(nfts_dir):
            return nfts

        for filename in os.listdir(nfts_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(nfts_dir, filename), 'r', encoding='utf-8') as f:
                        nft_data = json.load(f)
                        nfts.append(nft_data)
                except Exception as e:
                    logger.error(f"Error reading NFT file {filename}: {e}")

        return nfts

    def get_nft(self, user_id: int, nft_id: str) -> Optional[Dict]:
        """Получает NFT по ID"""
        user_dir = self.get_user_dir(user_id)
        nft_file = os.path.join(user_dir, "nfts", f"{nft_id}.json")

        if os.path.exists(nft_file):
            try:
                with open(nft_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading NFT {nft_id}: {e}")

        return None

    def update_nft(self, user_id: int, nft_data: Dict) -> bool:
        """Обновляет данные NFT"""
        return self.save_nft_metadata(user_id, nft_data)

    def _update_user_stats(self, user_id: int, nfts_created: int = 0, nfts_owned: int = 0):
        """Обновляет статистику пользователя"""
        try:
            user_dir = self.get_user_dir(user_id)
            stats_file = os.path.join(user_dir, "stats.json")

            stats = {
                "user_id": user_id,
                "nfts_created": nfts_created,
                "nfts_owned": nfts_owned,
                "last_updated": time.time()
            }

            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    existing_stats = json.load(f)
                    stats["nfts_created"] += existing_stats.get("nfts_created", 0)
                    stats["nfts_owned"] += existing_stats.get("nfts_owned", 0)

            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating user stats: {e}")