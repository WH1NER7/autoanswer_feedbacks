import datetime
import os
import requests
import json
import random
import logging
import pymorphy3
from openai import OpenAI

from chat_gpt_generation_ozon import generate_feedback_text_ozon
from ozon_feedbacks import process_url
from response_to_feedback import respond_to_review


def log_feedback_response(response_text, feedback):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "valuation": feedback.get("productValuation"),
        "feedback_id": feedback.get("id"),
        # "nmId": feedback.get('productDetails').get("nmId"),
        "response_text": response_text,
        "timestamp": timestamp,
        "feedback_text": feedback.get("text"),
        "user_name": feedback.get("userName")
    }

    with open("feedback_log.json", "a", encoding="utf-8") as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=2)


def get_token_evn(company):
    try:
        print(f'{company}_TOKEN')
        return os.environ[f'{company}_TOKEN']
    except Exception as e:
        print(e)
        return ''

#
def generate_feedback_text_wb(user_name, prod_val, feedback_text, has_photo):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Пример запроса
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",  # Имя вашей обученной модели
        temperature=0.9,
        max_tokens=1500,
        # top_p=0.9,
        # frequency_penalty=0.5,
        # presence_penalty=0.3
        messages=[
            {
                "role": "system",
                "content": (
                    "Вы — профессиональный менеджер по работе с клиентами компании MissYourKiss (мы продаем женское нижнее белье). "
                    "Ваша задача — вежливо и конструктивно отвечать на отзывы пользователей от лица компании. "
                    "Вам будет передаваться оценка товара пользователем, комментарий, плюс и минусы, которые выделил пользователь. А также оставил ли пользователь фото"

                    # Основные принципы
                    "Отвечайте покупателям на 'вы'. "
                    "Не превышайте 4 предложений в ответе. "
                    "Поддерживайте дружелюбный, но профессиональный тон общения. "
                    "Используйте 'теплый' стиль общения, как с давно знакомым клиентом, но без панибратства. "
                    "Используйте смайлы, если оценка товара — 5. "

                    # Обработка отзывов с низкими оценками (4 и ниже)
                    "Если отзыв содержит замечания по нашей вине "
                    "    - брак"
                    "    - недокомплект товара, обычно его воруют другие покупатели"
                    "    - выцветание ткани"
                    "то предложите покупателю связаться для решения проблемы. "
                    "Укажите следующие контакты (передавай полностью, как указано): "
                    "- Wildberries (Профиль -> Покупки -> Связаться с продавцом) "
                    "- t е l е g r а m: @missyourkiss_bot -> Служба заботы. "

                    # Недовольство товаром не по нашей вине
                    "Если клиент недоволен товаром не по нашей вине "
                    "    - товар провели как полученный на пункте выдачи, хотя клиент отказался"
                    "    - отсутствовали чокеры или подвязки, которые не должны входить в комплект"
                    "то выразите сожаление и объясните, что, к сожалению, такие ситуации случаются"

                    # Отзывы с высокой оценкой (5)
                    "Если отзыв имеет оценку 5 и текст положительный, и отзыв содержит фотографию, похвалите фотографию и скажите что-то приятное о ней. "

                    # Пустые отзывы
                    "Если отзыв пустой, поблагодарите за покупку и пригласите вернуться снова. "

                    # Имя клиента и завершение ответа
                    "Если имя клиента кажется ненастоящим, не используйте его в ответе. "
                    "В конце каждого ответа используйте одну из завершающих фраз, например: 'С любовью, MissYourKiss' или 'С наилучшими пожеланиями, MissYourKiss'. "

                    # Важно
                    "Никогда не обещайте создание или изменение товара. "
                    "Используйте красивое оформление текста с отступами. "
                    "Если текст отзыва пустой, отвечайте в зависимости от оценки."
                )
            },
            {
                "role": "user",
                "content": f"Клиента зовут {user_name}. Оценка {prod_val}. Есть ли фото?: {has_photo}. {feedback_text}"
            }
        ]
    )
    return response.choices[0].message.content


def get_unanswered_feedbacks(company):
    url = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks?isAnswered=false&take=1000&skip=0"

    token = get_token_evn(company)
    headers = {
        "Authorization": token
    }

    try:
        response = requests.get(url=url, headers=headers)
        print(response.json())
        return response.json().get('data').get('feedbacks')
    except Exception as e:
        print(e)
        return []


def answer_to_feedback(feedback_id, company, feedback_text, feedback):
    logging.info(f"Answering to feedback: {feedback_id} (Company: {company})")
    url = "https://feedbacks-api.wb.ru/api/v1/feedbacks"
    token = get_token_evn(company)

    headers = {
        "Authorization": token
    }
    body = {
        "id": feedback_id,
        "text": feedback_text
    }

    response = requests.patch(url=url, json=body, headers=headers)
    response_text = response.json()

    logging.info(f"Response for feedback {feedback_id}: {response_text}")
    log_feedback_response(feedback_text, feedback)
    print(feedback_text, response_text)


def get_wildberries_empty_feedbacks(cookie):
    url = "https://seller-services.wildberries.ru/ns/fa-seller-api/reviews-ext-back-end/api/v1/feedbacks?isAnswered=true&limit=100&offset=0&searchText=&sortOrder=dateDesc&valuations=1&valuations=2&valuations=3&valuations=4&valuations=5"

    headers = {
        'Cookie': cookie  # Укажите передаваемый cookie в заголовке
    }

    try:
        # Выполняем GET-запрос
        response = requests.get(url, headers=headers)

        # Проверка на успешность запроса
        if response.status_code != 200:
            print(f"Ошибка: не удалось получить данные. Статус код: {response.status_code}")
            return None

        # Преобразуем ответ в формат JSON
        data = response.json()

        # Проверка на наличие данных
        if data["data"]["feedbacks"]:
            feedbacks = data["data"]["feedbacks"]

            # Фильтруем отзывы, у которых поле "answer" равно null
            unanswered_feedbacks = [feedback for feedback in feedbacks if feedback['answer'] is None]

            return unanswered_feedbacks
        else:
            print("Ошибка: данные о отзывах отсутствуют в ответе.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def get_wildberries_unanswered_feedbacks(cookie):
    url = "https://seller-services.wildberries.ru/ns/fa-seller-api/reviews-ext-back-end/api/v1/feedbacks?isAnswered=false&limit=100&offset=0&searchText=&sortOrder=dateDesc&valuations=1&valuations=2&valuations=3&valuations=4&valuations=5"

    headers = {
        'Cookie': cookie  # Укажите передаваемый cookie в заголовке
    }

    try:
        # Выполняем GET-запрос
        response = requests.get(url, headers=headers)

        # Проверка на успешность запроса
        if response.status_code != 200:
            print(f"Ошибка: не удалось получить данные. Статус код: {response.status_code}")
            return None

        # Преобразуем ответ в формат JSON
        data = response.json()

        # Проверка на наличие данных
        if data["data"]["feedbacks"]:
            feedbacks = data["data"]["feedbacks"]

            # Фильтруем отзывы, у которых поле "answer" равно null
            # unanswered_feedbacks = [feedback for feedback in feedbacks if feedback['answer'] is None]

            return feedbacks
        else:
            print("Ошибка: данные о отзывах отсутствуют в ответе.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def answer_to_feedbacks_myk():
    for company in ["MissYourKiss"]:
        feedback_pool = get_wildberries_empty_feedbacks(os.getenv('MYK_COOKIE'))

        for feedback in feedback_pool:
            feedback_id = feedback.get('id')
            answer = generate_feedback_text_wb(feedback.get('feedbackInfo').get('userName'), feedback.get("valuation"), ("Текст: " + feedback.get('feedbackInfo').get("feedbackText", "") + '. Достоинства по мнению клиента: ' + feedback.get('feedbackInfo').get("feedbackTextPros", "") + '. Недостатки по мнению клиента: ' + feedback.get('feedbackInfo').get("feedbackTextCons", "")), bool(feedback.get('feedbackInfo').get('photos')))
            print(answer)
            answer_to_feedback(feedback_id, company, answer, feedback)

        feedback_pool_unanswered = get_wildberries_unanswered_feedbacks(os.getenv('MYK_COOKIE'))

        for feedback in feedback_pool_unanswered:
            feedback_id = feedback.get('id')
            answer = generate_feedback_text_wb(feedback.get('feedbackInfo').get('userName'), feedback.get("valuation"), ("Текст: " + feedback.get('feedbackInfo').get("feedbackText", "") + '. Достоинства по мнению клиента: ' + feedback.get('feedbackInfo').get("feedbackTextPros", "") + '. Недостатки по мнению клиента: ' + feedback.get('feedbackInfo').get("feedbackTextCons", "")), bool(feedback.get('feedbackInfo').get('photos')))
            print(answer)
            answer_to_feedback(feedback_id, company, answer, feedback)


def answer_to_feedbacks_myk_ozon():
    # Пример использования функции
    headers = {
        'Cookie': os.getenv('OZON_COOKIE'),
        # Замените на ваш реальный cookie
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
        "Accept-Language": "ru,en;q=0.9",
        "X-O3-Company-Id": "1043385"
    }

    feedback_pool = process_url(headers)
    for feedback in feedback_pool:
        uuid = feedback[0]

        feedback_text = generate_feedback_text_ozon(*feedback[1:])
        result = respond_to_review(uuid, feedback_text)
        print(result)


if __name__ == '__main__':
    # answer_to_feedbacks_all()
    answer_to_feedbacks_myk()
    answer_to_feedbacks_myk_ozon()

