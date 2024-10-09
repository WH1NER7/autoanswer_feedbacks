import os

import requests
import json


def respond_to_review(review_uuid, text):
    """
    Отправляет ответ на отзыв пользователя через API Ozon с дополнительными заголовками Cookie и X-O3-Company-Id.

    :param review_uuid: UUID отзыва, на который вы отвечаете
    :param text: Текст вашего ответа
    :param company_type: Тип компании (например, "seller")
    :param company_id: Идентификатор вашей компании
    :param access_token: Токен доступа для аутентификации
    :param cookie: Строка с куками для аутентификации
    :param x_o3_company_id: Идентификатор компании для заголовка X-O3-Company-Id
    :return: Ответ API в формате JSON или сообщение об ошибке
    """
    url = "https://seller.ozon.ru/api/review/comment/create"

    headers = {
        'Cookie': os.getenv('OZON_COOKIE'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
        "Accept-Language": "ru,en;q=0.9",
        "X-O3-Company-Id": "1043385"
    }

    body = {
        "review_uuid": review_uuid,
        "text": text,
        "company_type": "seller",
        "company_id": "1043385"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()  # Проверяет наличие HTTP ошибок
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка: {http_err} - {response.text}")
    except Exception as err:
        print(f"Произошла ошибка: {err}")
