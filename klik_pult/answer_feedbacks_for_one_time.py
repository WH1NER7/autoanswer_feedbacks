# import requests
# import json
# import os
#
# from klik_pult.chat_gpt_generation_ozon_klik import generate_feedback_text_ozon_klik
#
# # Заголовки и URL
# URL = "https://seller.ozon.ru/api/v3/review/list"
# HEADERS = {
#     'Cookie': os.getenv('OZON_COOKIE_KLIK'),
#     'Accept': 'application/json',
#     'X-O3-Company-Id': '419470',
#     'Content-Type': 'application/json',
# }
#
#
# # Тело запроса
# def get_reviews(pagination_last_timestamp=None, pagination_last_uuid=None):
#     payload = {
#         "with_counters": False,
#         "sort": {
#             "sort_by": "PUBLISHED_AT",
#             "sort_direction": "DESC"
#         },
#         "company_type": "seller",
#         "filter": {
#             "interaction_status": ["NOT_VIEWED"]
#         },
#         "company_id": "419470",
#         "pagination_last_timestamp": pagination_last_timestamp,
#         "pagination_last_uuid": pagination_last_uuid
#     }
#
#     response = requests.post(URL, headers=HEADERS, json=payload)
#
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Ошибка при получении отзывов: {response.status_code}")
#         return None
#
#
# def process_reviews(reviews_data):
#     reviews = []
#     for review in reviews_data.get('result', []):
#         # Фильтрация отзывов с статусом "NOT_VIEWED"
#         if review['interaction_status'] != "PROCESSED":
#             author_name = review['author_name']
#             rating = review['rating']
#             text = review['text']
#             pros = text.get('positive', 'Пользователь не оставил')
#             cons = text.get('negative', 'Пользователь не оставил')
#             comment = text.get('comment', 'Комментарий не оставлен')
#             photos_count = review['photos_count']
#             has_photo = True if photos_count > 0 else False
#             uuid = review['uuid']
#
#             review_text = f"Достоинства: {pros} | Недостатки: {cons} | Комментарий покупателя: {comment}"
#             reviews.append({
#                 'author_name': author_name,
#                 'rating': rating,
#                 'review_text': review_text,
#                 'has_photo': has_photo,
#                 'uuid': uuid
#             })
#     return reviews
#
#
# def respond_to_review(review_uuid, text):
#     url = "https://seller.ozon.ru/api/review/comment/create"
#     body = {
#         "review_uuid": review_uuid,
#         "text": text,
#         "company_type": "seller",
#         "company_id": "419470"
#     }
#
#     response = requests.post(url, headers=HEADERS, json=body)
#     if response.status_code == 200:
#         print(f"Ответ на отзыв с UUID {review_uuid} успешно отправлен.")
#     else:
#         print(f"Ошибка при отправке ответа на отзыв с UUID {review_uuid}: {response.text}")
#
#
# def process_all_reviews():
#     pagination_last_timestamp = None
#     pagination_last_uuid = None
#
#     while True:
#         reviews_data = get_reviews(pagination_last_timestamp, pagination_last_uuid)
#
#         if reviews_data is None:
#             break
#
#         # Обрабатываем отзывы
#         reviews = process_reviews(reviews_data)
#
#         # Ответы на отзывы
#         for review in reviews:
#             review_text = generate_feedback_text_ozon_klik(
#                 review['author_name'], review['rating'], review['review_text'], review['has_photo']
#             )
#             print(review_text)
#             respond_to_review(review['uuid'], review_text)
#
#         # Если есть следующая страница отзывов, получаем ее
#         if reviews_data.get("hasNext", False):
#             pagination_last_timestamp = reviews_data.get("pagination_last_timestamp")
#             pagination_last_uuid = reviews_data.get("pagination_last_uuid")
#         else:
#             break
#
# if __name__ == "__main__":
#     process_all_reviews()
