import logging
import os
import time

import requests
import telegram

from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')


def parse_homework_status(homework):
    verdicts = {
        'approved': (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
        ),
        'reviewing': 'Ваша работа взята в ревью',
        'rejected': 'К сожалению в работе нашлись ошибки.',
    }
    status = homework.get('status')
    homework_name = homework.get('homework_name')

    if status is None or homework_name is None:
        logging.error(
            f'Отсутствует статус или имя работы в ответе {homework}'
        )
        return f'В ответе сервера отсутствует статус или имя работы:\
            статус: {status}, имя работы: {homework_name}'

    verdict = verdicts.get(status)
    if verdict is not None:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    else:
        logging.error(
            f'Ошибка статуса: {status} не входит в {verdicts.keys()}'
        )

    return (f'Бот не узнаёт статус {status} вашей работы.')


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time()) - 86400

    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp}
        )
        return homework_statuses.json()

    except ValueError:
        logging.exception(
            f'Возникла ошибка, текст полученного ответа:\
                {homework_statuses.text}'
        )
        return {}
    except Exception as e:
        logging.exception(f'Ошибка {e} при получении ответа на запрос')
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
            current_timestamp = new_homework.get('current_date')
            time.sleep(1000)

        except Exception as e:
            logging.exception(f'Бот столкнулся с ошибкой: {e}')
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
