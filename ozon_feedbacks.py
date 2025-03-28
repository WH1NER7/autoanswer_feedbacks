import os

import requests
from bs4 import BeautifulSoup
import json


# Функция для обработки URL и парсинга данных отзывов
# def process_url(headers):
#     response = requests.get("https://seller.ozon.ru/app/reviews", headers=headers)
#     feedback_pool = []
#     if response.status_code == 200:
#
#         html_content = response.text
#         soup = BeautifulSoup(html_content, 'html.parser')
#         script_tags = soup.find_all('script')
#
#         # Ищем теги script с содержимым window.__MODULE_STATE__
#         for script_tag in script_tags:
#             if script_tag.string and 'window.__MODULE_STATE__' in script_tag.string:
#                 script_content = script_tag.string.strip()
#
#                 json_str = script_content.replace('(window.__MODULE_STATE__=window.__MODULE_STATE__||{})["reviews"]=',
#                                                   '').rstrip(';')
#
#                 try:
#                     # Преобразуем строку в JSON объект
#                     extracted_json = json.loads(json_str)
#
#                     # Достаем отзывы
#                     reviews_data = extracted_json.get("reviews").get('buyerReviews').get('reviews')
#                     if reviews_data:
#                         for review in reviews_data:
#
#                             review_id = review.get('id')
#                             rating = review.get('rating')
#                             author_name = review.get('authorName')
#                             text = review.get('text', {})
#                             positive = text.get('positive', 'Нет плюсов')
#                             negative = text.get('negative', 'Нет минусов')
#                             comment = text.get('comment', 'Нет комментария')
#                             product_title = review.get('product', {}).get('title', 'Неизвестный товар')
#                             product_url = review.get('product', {}).get('url', '#')
#                             published_at = review.get('publishedAt')
#                             uuid = review.get('uuid')
#                             is_answered = get_review_comments(uuid, headers)
#                             if is_answered.get('result') == []:
#                                 feedback_pool.append([uuid, author_name, rating, "Текст: " + comment + '. Достоинства по мнению клиента: ' + positive + '. Недостатки по мнению клиента: ' + negative, False])
#                             # return uuid, author_name, rating, "Текст: " + comment + '. Достоинства по мнению клиента: ' + positive + '. Недостатки по мнению клиента: ' + negative, False
#                 except json.JSONDecodeError as e:
#                     print(f"Ошибка при преобразовании в JSON: {e}")
#         return feedback_pool
#     else:
#         print(f"Ошибка запроса: {response.status_code}")
#
#
# def get_review_comments(review_uuid, headers):
#     """
#     Функция для отправки POST-запроса к API Ozon для получения списка комментариев к отзыву.
#
#     :param review_uuid: UUID отзыва, для которого необходимо получить комментарии.
#     :param company_id: Идентификатор компании.
#     :param company_type: Тип компании (например, "seller").
#     :param access_token: Токен доступа для аутентификации.
#     :return: Ответ API в формате JSON или сообщение об ошибке.
#     """
#     url = "https://seller.ozon.ru/api/v2/review/comment/list"
#
#     body = {
#         "review_uuid": review_uuid,
#         "company_type": "seller",
#         "company_id": "1043385"
#     }
#
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(body))
#         response.raise_for_status()  # Проверка на наличие HTTP ошибок
#         return response.json()
#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP ошибка: {http_err} - {response.text}")
#     except Exception as err:
#         print(f"Произошла ошибка: {err}")
#         return None

# print(get_review_comments("019271b5-f4fb-703d-997d-7444f403a235"))


import os
import requests

def get_reviews(headers):
    # Замените на ваш реальный cookie и company_id
    # OZON_COOKIE = os.getenv('OZON_COOKIE')
    COMPANY_ID = '1043385'  # Замените на ваш реальный company_id

    url = 'https://seller.ozon.ru/api/v3/review/list'

    # Тело запроса
    payload = {
        "with_counters": False,
        "sort": {
            "sort_by": "PUBLISHED_AT",
            "sort_direction": "DESC"
        },
        "company_type": "seller",
        "filter": {
            "interaction_status": ["NOT_VIEWED"]
        },
        "company_id": COMPANY_ID,
        "pagination_last_timestamp": None,
        "pagination_last_uuid": None
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        # Проверяем, есть ли 'result' в ответе
        if 'result' in data:
            reviews = []
            for item in data['result']:
                uuid = item.get('uuid', '')
                author_name = item.get('author_name', '')
                rating = item.get('rating', '')
                text_data = item.get('text', {})
                positive = text_data.get('positive', '')
                negative = text_data.get('negative', '')
                comment = text_data.get('comment', '')

                full_text = (
                    f"Текст: {comment}. "
                    f"Достоинства по мнению клиента: {positive}. "
                    f"Недостатки по мнению клиента: {negative}."
                )

                reviews.append([uuid, author_name, rating, full_text, False])

            return reviews
        else:
            print("Поле 'result' отсутствует в ответе.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return []
