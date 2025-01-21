import requests
import os
import time
import json
import logging
from datetime import datetime, timedelta
import pytz

CLIENT_ID = "419470"
API_KEY = os.getenv("KLIK_API_MSG")

# Базовые настройки
BASE_URL = 'https://api-seller.ozon.ru'
HEADERS = {
    'Client-Id': CLIENT_ID,
    'Api-Key': API_KEY,
    'Content-Type': 'application/json'
}

# Настройка логирования
logging.basicConfig(
    filename='auto_reply.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Файл для хранения обработанных чатов (где уже отправлен автоответ)
AUTO_REPLY_FILE = 'auto_replied_chats.json'


def load_auto_replied_chats():
    if os.path.exists(AUTO_REPLY_FILE):
        with open(AUTO_REPLY_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_auto_replied_chats(auto_replied):
    with open(AUTO_REPLY_FILE, 'w') as f:
        json.dump(list(auto_replied), f)


def get_opened_chats():
    url = f"{BASE_URL}/v2/chat/list"
    body = {
        "filter": {
            "chat_status": "Opened",
            "unread_only": False
        },
        "limit": 30,
        "offset": 0
    }
    response = requests.post(url, json=body, headers=HEADERS)
    response.raise_for_status()
    return response.json().get('chats', [])


def get_chat_history(chat_id):
    url = f"{BASE_URL}/v2/chat/history"
    body = {
        "chat_id": chat_id,
        "direction": "Backward",
        "from_message_id": 0,  # Начинаем с самого начала
        "limit": 1000  # Увеличиваем лимит для полной истории
    }
    response = requests.post(url, json=body, headers=HEADERS)
    response.raise_for_status()
    return response.json().get('messages', [])


def send_auto_reply(chat_id, text):
    url = f"{BASE_URL}/v1/chat/send/message"
    body = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=body, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def process_chats(auto_replied):
    try:
        chats = get_opened_chats()
        logging.info(f"Получено {len(chats)} открытых чатов.")

        for chat in chats:
            if chat.get('chat_type') != 'Buyer_Seller':
                continue

            chat_id = chat.get('chat_id')

            # Проверяем, был ли уже отправлен автоответ в этот чат
            if chat_id in auto_replied:
                logging.info(f"Автоответ уже отправлен в чат {chat_id}. Пропуск.")
                continue

            messages = get_chat_history(chat_id)
            if not messages:
                logging.info(f"Нет сообщений в чате {chat_id}. Пропуск.")
                continue

            # Проверяем наличие сообщений от продавца
            seller_has_replied = False
            for message in messages:
                user_type = message.get('user', {}).get('type')
                if user_type == 'Seller':
                    seller_has_replied = True
                    break

            if seller_has_replied:
                logging.info(f"В чате {chat_id} уже есть сообщение от продавца. Пропуск.")
                continue

            # Если продавец не отвечал, проверяем дату последнего сообщения от клиента
            # Находим последнее сообщение от клиента
            last_customer_message = None
            for message in reversed(messages):
                if message.get('user', {}).get('type') == 'Customer':
                    last_customer_message = message
                    break

            if last_customer_message:
                # Парсим дату сообщения
                message_time_str = last_customer_message.get('created_at')
                message_time = datetime.strptime(message_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                message_time = message_time.replace(tzinfo=pytz.UTC)

                # Текущее время в UTC
                current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

                # Разница во времени
                time_diff = current_time - message_time

                if time_diff <= timedelta(weeks=1):
                    # Отправляем автоответ
                    auto_reply_text = "Здравствуйте! Мы рады, что вы обратились именно к нам.\n\
Ваша информация принята в работу и передана в отдел технической поддержки. Ответ на ваш запрос поступит оперативно в течение 2–4 часов с понедельника по пятницу с 9:00 до 18:00. В выходные дни ответ может задержаться до нескольких часов.\n\
Не спешите оформлять возврат и отказываться от товара. По внутренней статистике, мы помогаем решить 95% всех обращений по неполадкам в ходе переписки, но все решения выносим в пользу покупателя.\n\
Спасибо, что выбираете нас, с уважением, интернет-магазин Klik_Pult"
                    send_auto_reply(chat_id, auto_reply_text)
                    logging.info(
                        f"Отправлен автоответ в чат {chat_id} на сообщение {last_customer_message.get('message_id')}.")
                    # Добавляем чат в обработанные
                    auto_replied.add(chat_id)
                else:
                    logging.info(f"Последнее сообщение в чате {chat_id} старше недели. Пропуск автоответа.")
            else:
                logging.info(f"В чате {chat_id} нет сообщений от клиента. Пропуск.")

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP ошибка: {http_err}")
    except Exception as err:
        logging.error(f"Ошибка: {err}")


def answer_forgotten_users():
    auto_replied = load_auto_replied_chats()
    logging.info("Скрипт автоответа запущен.")
    process_chats(auto_replied)
    save_auto_replied_chats(auto_replied)


