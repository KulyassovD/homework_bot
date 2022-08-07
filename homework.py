import logging
import os
import time
import requests
import telegram
import exceptions

from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as error:
        logging.error(f'Не удалось отправить сообщение {error}')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.InaccessibilityAPIError
        return response.json()
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    try:
        homework_statuses = response.get('homeworks')
        return homework_statuses
    except Exception as error:
        logging.error(f'отсутствие ожидаемых ключей в ответе API {error}')


def parse_status(homework):
    try:
        homework_name = homework[0]['homework_name']
    except Exception as error:
        logging.error(f'отсутсвует нужный ключ {error}')
    try:
        verdict = HOMEWORK_STATUSES[homework[0]['status']]
    except Exception as error:
        logging.error(f'отсутсвует нужный ключ-статус {error}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    logging.info('Запущена функция "check_tokens"')
    tokens = ("PRACTICUM_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")

    for name in tokens:
        if not globals()[name]:
            logging.critical(f"Не задано значение для {name}")
            return False

    return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 2629743)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            cash = message
            if cash != message:
                send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()