import datetime
import os
import requests
import json
import random
import logging
from openai import OpenAI
from datetime import datetime, timedelta

from chat_gpt_generation_ozon import generate_feedback_text_ozon
from klik_pult.answer_feedbacks_for_one_time import process_all_reviews
from ozon_feedbacks import get_reviews
from response_to_feedback import respond_to_review
from test_chat_ozon_answer import answer_forgotten_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                    "Вам будет передаваться оценка товара пользователем, комментарий, плюсы и минусы, которые выделил пользователь. А также оставил ли пользователь фото"

                    # Основные принципы
                    "Отвечайте покупателям на 'вы'. "
                    "Не превышайте 4 предложений в ответе. "
                    "Поддерживайте дружелюбный, но профессиональный тон общения. "
                    "Используйте 'теплый' стиль общения, как с давно знакомым клиентом, но без панибратства."
                    "Используйте смайлы, если оценка товара — 5. "

                    # Обработка отзывов с низкими оценками (4 и ниже)
                    "Если отзыв содержит замечания по нашей вине:"
                    "  - брак"
                    "  - недокомплект товара(клиент не получил какую то часть комплекта)"
                    "  - выцветание ткани"
                    "Поблагодарите за отзыв, объясните что все товары перед отправкой проходят тщательную проверку качества (если брак) "
                    "и проверяются на комплектность (если клиент обращается с недокомплектом)"
                    "и предложите покупателю связаться для решения проблемы."
                    "НЕ ОПРАВДЫВАТЬ ПРОБЛЕМЫ фразой что такие ситуации иногда могут происходить"
                    "Укажите следующие контакты (передавай полностью, как указано, обязательно пиши t e l e g r a m раздельными буквами): "
                    "- Wildberries (Профиль -> Покупки -> Связаться с продавцом) "
                    "- t е l е g r а m: @missyourkiss_bot -> Служба заботы. "

                    # Недовольство товаром не по нашей вине
                    "Если клиент недоволен товаром не по нашей вине "
                    "    - товар провели как полученный на пункте выдачи, хотя клиент отказался"
                    "    - отсутствовали чокеры или подвязки(клиент ПРЯМО говорит что не получил чокер или подвязки)"
                    "то выразите сожаление и объясните, что, к сожалению, такие ситуации случаются"


                    # Проблема со стиркой не по нашей вине
                    "Если клиент сообщает о проблемах с изделием после стирки, не связанной с производственным браком,"
                    "выразите сожаление о возникшей ситуации и объясните, что деликатные ткани требуют особого ухода."
                    "Сообщите, что все изделия проходят множество тестов, включая стирку, и что для сохранения качества"
                    "необходимо строго следовать символам на бирке изделия, стирать на деликатном режиме при температуре не выше 30 градусов,"
                    "и стирать отдельно от других вещей, чтобы сохранить цвет и структуру изделия в идеальном состоянии."
                    "Объясните, что изделия из деликатных тканей и фурнитуры не рассчитаны на высокие температуры и интенсивный отжим,"
                    "что может приводить к повреждению ткани и потере цвета. Завершите благодарностью за понимание и надеждой на следующие покупки."


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
def answer_to_feedback(feedback_id, company, feedback_text):
    logging.info(f"Answering to feedback: {feedback_id} (Company: {company})")
    url = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks/answer"
    token = get_token_evn(company)

    headers = {
        "Authorization": token
    }
    body = {
        "id": feedback_id,
        "text": feedback_text
    }

    response = requests.patch(url=url, json=body, headers=headers)
    print(response.status_code)


def get_combined_unanswered_feedbacks(API_KEY):
    # Вычисляем дату два дня назад в формате Unix
    two_days_ago_unix = int((datetime.utcnow() - timedelta(days=2)).timestamp())

    base_url = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
    params_list = [
        {'isAnswered': 'true', 'take': 5000, 'skip': 0, 'dateFrom': two_days_ago_unix},
        {'isAnswered': 'false', 'take': 5000, 'skip': 0, 'dateFrom': two_days_ago_unix}
    ]

    headers = {
        "Authorization": API_KEY
    }

    combined_feedbacks = []

    for params in params_list:
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Ошибка при запросе с параметрами {params}: {response.status_code}")
            continue  # Переходим к следующему запросу

        try:
            response_data = response.json()
        except ValueError:
            print(f"Невозможно декодировать JSON для параметров {params}")
            continue

        # Извлекаем список отзывов
        feedbacks = response_data.get("data", {}).get("feedbacks", [])

        # Фильтруем отзывы, у которых answer == null
        unanswered_feedbacks = [f for f in feedbacks if f.get("answer") is None]

        combined_feedbacks.extend(unanswered_feedbacks)

    return combined_feedbacks


# def process_and_answer_feedbacks():
#     feedbacks = get_combined_unanswered_feedbacks(os.getenv('MissYourKiss_TOKEN'))
#     logger.info(f"Всего неотвеченных отзывов для обработки: {len(feedbacks)}")
#
#     for feedback in feedbacks:
#         feedback_id = feedback.get('id')
#         user_name = feedback.get('userName', 'Пользователь')
#         product_valuation = feedback.get('productValuation', 'N/A')
#         text = feedback.get('text', '').strip()
#         pros = feedback.get('pros', '').strip()
#         cons = feedback.get('cons', '').strip()
#         photo_links = feedback.get('photoLinks', [])
#
#         # Формируем текст отзыва
#         feedback_text = f"Текст: {text}. Достоинства по мнению клиента: {pros}. Недостатки по мнению клиента: {cons}"
#
#         # Генерируем ответ
#         answer = generate_feedback_text_wb_before_NY(
#             user_name=user_name,
#             prod_val=product_valuation,
#             feedback_text=feedback_text,
#             has_photo=bool(photo_links)
#         )
#
#         # Отправляем ответ
#         try:
#             answer_to_feedback(feedback_id, 'MissYourKiss', answer)
#         except Exception as e:
#             logger.error(f"Ошибка при отправке ответа для отзыва ID: {feedback_id}. Ошибка: {e}")


def process_and_answer_feedbacks():
    feedbacks = get_combined_unanswered_feedbacks(os.getenv('MissYourKiss_TOKEN'))
    logger.info(f"Всего неотвеченных отзывов для обработки: {len(feedbacks)}")

    # Определяем текущую дату
    today = datetime.utcnow().date()

    # Определяем границы дат
    before_ny_end = datetime(2024, 12, 31).date()
    ny_start = datetime(2024, 12, 31).date()
    ny_end = datetime(2025, 1, 18).date()

    for feedback in feedbacks:
        feedback_id = feedback.get('id')
        user_name = feedback.get('userName', 'Пользователь')
        product_valuation = feedback.get('productValuation', 'N/A')
        text = feedback.get('text', '').strip()
        pros = feedback.get('pros', '').strip()
        cons = feedback.get('cons', '').strip()
        photo_links = feedback.get('photoLinks', [])

        # Формируем текст отзыва
        feedback_text = f"Текст: {text}. Достоинства по мнению клиента: {pros}. Недостатки по мнению клиента: {cons}"

        # Выбор функции генерации ответа в зависимости от текущей даты
        answer = generate_feedback_text_wb(
            user_name=user_name,
            prod_val=product_valuation,
            feedback_text=feedback_text,
            has_photo=bool(photo_links)
        )

        try:
            answer_to_feedback(feedback_id, 'MissYourKiss', answer)
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа для отзыва ID: {feedback_id}. Ошибка: {e}")


def answer_to_feedbacks_myk_ozon():
    # Пример использования функции
    headers = {
        'Cookie': os.getenv('OZON_COOKIE'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
        "Accept-Language": "ru,en;q=0.9",
        "X-O3-Company-Id": "1043385"
    }

    feedback_pool = get_reviews(headers)
    for feedback in feedback_pool:
        uuid = feedback[0]

        feedback_text = generate_feedback_text_ozon(*feedback[1:])
        result = respond_to_review(uuid, feedback_text)
        print(result)


def answer_to_feedbacks_klik_pult_ozon():
    # Пример использования функции
    process_all_reviews()


if __name__ == '__main__':
    try:
        answer_to_feedbacks_myk_ozon()
    except Exception as e:
        print(e)

    try:
        process_and_answer_feedbacks()
    except Exception as e:
        print(e)

    try:
        answer_to_feedbacks_klik_pult_ozon()
    except Exception as e:
        print(e)

    try:
        answer_forgotten_users()
    except Exception as e:
        print(e)
