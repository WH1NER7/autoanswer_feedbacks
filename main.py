import datetime
import os
import requests
import json
import random
import logging
import pymorphy3
from openai import OpenAI


def log_feedback_response(response_text, feedback):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "valuation": feedback.get("productValuation"),
        "feedback_id": feedback.get("id"),
        "nmId": feedback.get('productDetails').get("nmId"),
        "response_text": response_text,
        "timestamp": timestamp,
        "feedback_text": feedback.get("text"),
        "user_name": feedback.get("userName")
    }

    with open("feedback_log.json", "a", encoding="utf-8") as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=2)


def get_token_evn(company):
    try:
        return os.environ[f'{company}_TOKEN']
    except Exception as e:
        print(e)
        return ''

#
def generate_feedback_text(user_name, prod_val, feedback_text, has_photo):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Пример запроса
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",  # Имя вашей обученной модели
        temperature=0.7,
        # max_tokens=100,
        # top_p=0.9,
        # frequency_penalty=0.5,
        # presence_penalty=0.3
        messages=[
            {
                "role": "system",
                "content": (
                    "Вы — профессиональный менеджер по работе с клиентами компании MissYourKiss (мы продаем женское нижнее белье). "
                    "Ваша задача — вежливо и конструктивно отвечать на отзывы пользователей от лица компании. "
                    
                    # Основные принципы
                    "Отвечайте покупателям на 'вы'. "
                    "Не превышайте 4 предложений в ответе. "
                    "Поддерживайте дружелюбный, но профессиональный тон общения. "
                    "Используйте 'теплый' стиль общения, как с давно знакомым клиентом, но без панибратства. "
                    "Используйте смайлы, если оценка товара — 5. "
                    
                    # Обработка отзывов с низкими оценками (4 и ниже)
                    "Если отзыв содержит замечания по нашей вине (например, брак или недокомплект товара, обычно его воруют другие покупатели), предложите покупателю связаться для решения проблемы. "
                    "Укажите следующие контакты (передавай полностью, как указано): "
                    "- Wildberries (Профиль -> Покупки -> Связаться с продавцом) "
                    "- Telegram: @missyourkiss_bot -> Служба заботы. "
                    
                    # Недовольство товаром не по нашей вине
                    "Если клиент недоволен товаром не по нашей вине (например, товар провели как полученный на пункте выдачи, хотя клиент отказался, или отсутствовали чокеры или подвязки, которые не должны входить в комплект), выразите сожаление и объясните, что не всегда всё подходит всем. "
                    
                    # Отзывы с высокой оценкой (5)
                    "Если отзыв имеет оценку 5 и текст положительный, и если отзыв содержит фотографию, похвалите фотографию и скажите что-то приятное о ней. "
                    
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


def answer_to_feedbacks_myk():
    for company in ["MissYourKiss"]:
        feedback_pool = get_unanswered_feedbacks(company)

        for feedback in feedback_pool:
            feedback_id = feedback.get('id')
            print("Текст: " + feedback.get("text", "") + ' | Плюсы, которые выделил пользователь: ' + feedback.get("pros", "") + ' | Минусы, которые выделил пользователь: ' + feedback.get("cons", ""))
            answer = generate_feedback_text(feedback.get('userName'), feedback.get("productValuation"), ("Текст: " + feedback.get("text", "") + '. Достоинства по мнению клиента: ' + feedback.get("pros", "") + '. Недостатки по мнению клиента: ' + feedback.get("cons", "")), bool(feedback.get('photoLinks')))
            print(answer)
            answer_to_feedback(feedback_id, company, answer, feedback)


if __name__ == '__main__':
    # answer_to_feedbacks_all()
    answer_to_feedbacks_myk()
