import datetime
import os
import requests
import json
import random
import logging


def log_feedback_response(response_text, feedback, feedback_text):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "feedback": feedback,
        "response_text": response_text,
        "timestamp": timestamp,
        "feedback_text": feedback_text
    }

    with open("feedback_log.json", "a", encoding="utf-8") as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=2)


def get_token_evn(company):
    try:
        return os.environ[f'{company}_TOKEN']
    except Exception as e:
        print(e)
        return ''


def get_feedback_text(company_name, user_name, category):
    json_file_path = 'texts.json'

    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    random_text = random.choice(data[category])
    updated_text = random_text.replace("(ИМЯ)", user_name)
    updated_text = updated_text.replace("MissYourKiss", company_name)

    return updated_text
    # print(random_text)


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
    log_feedback_response(response_text, feedback, feedback_text)
    print(feedback_text, response_text)


def main():
    # for company in ['Bonasita', 'MissYourKiss']:
    for company in ['Bonasita']:
        feedback_pool = get_unanswered_feedbacks(company)
        for feedback in feedback_pool:
            print(feedback)
            if feedback['productValuation'] == 5:
                text = ''
                feedback_id = feedback.get('id')
                user_name = feedback.get('userName')
                has_user_name = bool(feedback.get('userName'))
                has_photo = bool(feedback.get('photoLinks'))
                if has_photo and has_user_name:
                    text = get_feedback_text(company, user_name, "name_image")
                elif has_photo and not has_user_name:
                    text = get_feedback_text(company, user_name, "anon_images")
                elif not has_photo and has_user_name:
                    text = get_feedback_text(company, user_name, "no_photos_name")
                elif not has_photo and not has_user_name:
                    text = get_feedback_text(company, user_name, "anon_no_photo")

                if text:
                    pass
                    answer_to_feedback(feedback_id, company, text, feedback)


def answer_to_empty_feedbacks_myk():
    for company in ['MissYourKiss']:
        feedback_pool = get_unanswered_feedbacks(company)
        for feedback in feedback_pool:
            # print(feedback)
            if feedback['productValuation'] == 5 and feedback['text'] == '':
                text = ''
                feedback_id = feedback.get('id')
                user_name = feedback.get('userName')
                has_user_name = bool(feedback.get('userName'))
                has_photo = bool(feedback.get('photoLinks'))
                if has_photo and has_user_name:
                    text = get_feedback_text(company, user_name, "name_image")
                elif has_photo and not has_user_name:
                    text = get_feedback_text(company, user_name, "anon_images")
                elif not has_photo and has_user_name:
                    text = get_feedback_text(company, user_name, "no_photos_name")
                elif not has_photo and not has_user_name:
                    text = get_feedback_text(company, user_name, "anon_no_photo")

                if text:
                    pass
                    answer_to_feedback(feedback_id, company, text, feedback)


if __name__ == '__main__':
    answer_to_empty_feedbacks_myk()
    # print(get_feedback_text('Bonasita', '', "anon_images"))
    # print(get_feedback_text('Bonasita', '', "anon_no_photo"))
    # print(get_feedback_text('Bonasita', 'ывы', "name_image"))
    # print(get_feedback_text('Bonasita', 'ывы', "no_photos_name"))
    main()
