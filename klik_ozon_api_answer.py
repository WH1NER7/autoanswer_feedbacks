import os

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

from klik_pult.chat_gpt_generation_ozon_klik import generate_feedback_text_ozon_klik

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('feedback_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Общие настройки
HEADERS = {
    "Content-Type": "application/json",
    "Api-Key": os.getenv("KLIK_OZON_API_FEEDBACKS"),
    "Client-Id": "419470"
}
BASE_URL = "https://api-seller.ozon.ru/v1/review"


def get_unprocessed_reviews() -> Optional[List[Dict]]:
    """Получение непрочитанных отзывов"""
    try:
        response = requests.post(
            f"{BASE_URL}/list",
            headers=HEADERS,
            json={
                  "limit": 100,
                  "sort_dir": "DESC",
                  "status": "UNPROCESSED"
                }
            )
        response.raise_for_status()

        reviews = response.json().get('reviews', [])
        filtered_reviews = [
            review for review in reviews
            if review.get('status') == 'UNPROCESSED'
               and datetime.fromisoformat(review['published_at']).year >= 2025  # >= вместо <=
        ]

        return filtered_reviews

    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        return None


def post_comment(review_id: str, text: str) -> bool:
    """Публикация комментария к отзыву"""
    try:
        payload = {
            "mark_review_as_processed": True,
            "review_id": review_id,
            "text": text
        }

        response = requests.post(
            f"{BASE_URL}/comment/create",
            headers=HEADERS,
            json=payload
        )

        if response.status_code == 200:
            logger.info(f"Successfully posted comment for review {review_id}")
            return True

        logger.error(f"Failed to post comment: {response.text}")
        return False

    except Exception as e:
        logger.error(f"Error posting comment: {str(e)}")
        return False


def process_reviews():
    """Основная функция обработки отзывов"""
    reviews = get_unprocessed_reviews()

    if not reviews:
        logger.info("No unprocessed reviews found")
        return

    for review in reviews:
        try:
            review_id = review['id']
            rating = review['rating']
            photos = review['photos_amount'] > 0
            videos = review['videos_amount'] > 0
            text = review.get('text', '')

            # Генерируем текст ответа
            response_text = generate_feedback_text_ozon_klik(
                user_name='',
                prod_val=rating,
                feedback_text=text,
                has_photo=photos,
                has_video=videos
            )

            # Отправляем комментарий
            success = post_comment(review_id, response_text)

            if not success:
                logger.warning(f"Failed to process review {review_id}")

        except KeyError as e:
            logger.error(f"Missing key in review data: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing review {review_id}: {str(e)}")


# if __name__ == "__main__":
#     logger.info("Starting feedback processing")
#     process_reviews()
#     logger.info("Processing completed")
