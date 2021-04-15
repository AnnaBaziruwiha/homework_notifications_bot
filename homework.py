import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    status = homework.get('status')
    if status is None:
        return 'Бот не может найти домашку в ответе сервиса.'

    verdicts = {
        'approved': (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
        ),
        'reviewing': 'Ваша работа взята в ревью',
        'rejected': 'К сожалению в работе нашлись ошибки.',
    }
    homework_name = homework.get('homework_name')

    if status in verdicts.keys():
        verdict = verdicts[status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    else:
        return 'Бот не узнаёт статус вашей работы.'


def get_homework_statuses(current_timestamp):
    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp}
        )
    except Exception as e:
        logging.exception(f'Ошибка {e} при получении ответа на запрос')

    try:
        return homework_statuses.json()
    except ValueError:
        logging.exception('Формат ответа не совпадает с ожидаемым')
        return {}


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(name)s: %(funcName)s: %(message)s'
    )
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]),
                    bot_client
                )
            if new_homework.get('current_date'):
                current_timestamp = new_homework.get('current_date')
            else:
                current_timestamp = int(time.time())
            time.sleep(1190)

        except Exception as e:
            logging.exception(f'Бот столкнулся с ошибкой: {e}')
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
