import datetime
import os
import requests
import json
import random
import logging
import pymorphy3


def detect_name_and_gender(name):
    first_name = name.split(" ")[0]
    morph = pymorphy3.MorphAnalyzer(lang='ru')
    parsed_name = morph.parse(first_name)
    print(parsed_name)

    score_male = 0
    score_female = 0
    score_surn = 0

    for result in parsed_name:
        if 'Name' in result.tag and "femn" in result.tag and result.normal_form == first_name.lower():
            score_female += result.score
        elif 'Name' in result.tag and "masc" in result.tag and result.normal_form == first_name.lower():
            score_male += result.score
        elif 'Surn' in result.tag:
            score_surn += result.score

    print(name, score_female, score_male, score_surn)
    if score_male > 0.7 and score_male > score_female:
        return 'male'
    elif score_surn > score_male + score_female:
        return 'unknown'
    elif score_female > score_male:  # Если фамилия встречается чаще, чем имя
        return 'female'
    else:
        return 'unknown'


def get_feedback_text_category(has_photo, has_user_name, sex, valuation):
    if valuation < 5:
        return "negative"

    categories = {
        (True, True, 'male'): "name_image_male",
        (True, True, 'female'): "name_image_female",
        (True, False, 'female'): "anon_images_female",
        (False, True, 'male'): "no_photos_name_male",
        (False, True, 'female'): "no_photos_name_female",
        (False, False, 'male'): "anon_no_photo_male",
        (False, False, 'female'): "anon_no_photo_female",
        (False, True, 'unknown'): "anon_no_photo_female",
        (True, True, 'unknown'): "name_image_female",
        (True, False, 'unknown'): "anon_images_female",
        (False, False, 'unknown'): "anon_no_photo_female",
    }

    return categories.get((has_photo, has_user_name, sex), "no_photos_name_female")


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


def get_feedback_text(company, user_name, category):
    json_file_path = f'texts_{company}.json'

    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    random_text = random.choice(data[category])
    updated_text = random_text.replace("(ИМЯ)", user_name)
    updated_text = updated_text.replace("MissYourKiss", company)

    return updated_text


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


def answer_to_feedbacks_all():
    for company in ["Bonasita"]:
        feedback_pool = get_unanswered_feedbacks(company)

        for feedback in feedback_pool:
            if feedback.get("productValuation") == 5:
                feedback_id = feedback.get('id')
                user_name = feedback.get('userName')
                has_user_name = bool(feedback.get('userName'))
                has_photo = bool(feedback.get('photoLinks'))
                sex = detect_name_and_gender(user_name)

                text_category = get_feedback_text_category(has_photo, has_user_name, sex,
                                                           feedback.get("productValuation"))
                text = get_feedback_text(company, user_name, text_category)

                answer_to_feedback(feedback_id, company, text, feedback)


import re


def answer_to_feedbacks_myk():
    banned_words = [
        "перепутали", "отказалась", "изнашиваются", "на маленькую грудь", "порвались",
        "в комплекте нет", "материал не дышит", "не подошел в объеме", "большой в объеме",
        "отдала предпочтение другому", "нитки торчат", "маломерит", "маломер", "мал",
        "отказ", "в пользу другой модели", "бюст маловат", "лифчик маленький", "лифон маленький",
        "лифчик малюсенький", "чашки маленькие", "возврат", "не подошли", "выглядят истрепавшимися",
        "повылазили нитки", "дорого", "дороговато"
    ]

    morph = pymorphy3.MorphAnalyzer()

    def get_all_forms(word):
        parsed_word = morph.parse(word)[0]
        return {form.word for form in parsed_word.lexeme}

    banned_forms = set()
    for word in banned_words:
        forms = get_all_forms(word)
        banned_forms.update(forms)

    def contains_banned_word(feedback_text):
        feedback_text_lower = feedback_text.lower()
        for word in banned_forms:
            pattern = rf'\b{re.escape(word)}\b'
            if re.search(pattern, feedback_text_lower):
                return True
        return False

    for company in ["MissYourKiss"]:
        feedback_pool = get_unanswered_feedbacks(company)

        for feedback in feedback_pool:
            feedback_text = feedback.get("text", "")
            # Проверяем, что текст отзыва не содержит запрещенных слов
            if contains_banned_word(feedback_text):
                continue

            # Проверяем, что оценка равна максимальной и нет ссылок на фотографии
            if feedback.get("productValuation") == 5 and not bool(feedback.get('photoLinks')) and not feedback.get('productDetails').get("nmId") in [218272630, 226609837, 226609836, 241885224, 226608461, 228738081]:
                feedback_id = feedback.get('id')
                user_name = feedback.get('userName')
                has_user_name = bool(feedback.get('userName'))
                has_photo = bool(feedback.get('photoLinks'))
                sex = detect_name_and_gender(user_name)

                text_category = get_feedback_text_category(has_photo, has_user_name, sex,
                                                           feedback.get("productValuation"))
                text = get_feedback_text(company, user_name, text_category)

                answer_to_feedback(feedback_id, company, text, feedback)


if __name__ == '__main__':
    # answer_to_feedbacks_all()
    answer_to_feedbacks_myk()
