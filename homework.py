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
    """Отправка сообщений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as error:
        logging.error(f'Не удалось отправить сообщение {error}')


def get_api_answer(current_timestamp):
    """Запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        logging.error('Ошибка при запросе к основному API')
        raise exceptions.APIError
    else:
        return response.json()


def check_response(response):
    """Проверка полученного ответа от API."""
    if len(response) == 0:
        logging.error('Ответ от API содержит пустой словарь')
        raise exceptions.ResponseDicIsEmptyException
    if response['homeworks'] is False:
        logging.error('Словарь в ответе от API не содержит ключ `homeworks`')
        raise exceptions.ResponseDicNotContainHomeworkKeyException
    if not isinstance(response['homeworks'], list):
        logging.error('Под ключом `homeworks` ДР приходят не в виде списка')
        raise exceptions.ResponseKeyHomeworksIsNotListException
    if len(response['homeworks']) == 0:
        return 0
    return response['homeworks']


def parse_status(homework):
    """Получение статуса."""
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
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
            homework = check_response(response)[0]
            message = parse_status(homework)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
