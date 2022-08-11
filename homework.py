import logging
import os
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

try:
    from simplejson.errors import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError

import exceptions

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)

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
    logger.info('Запущена функция send_message"')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except telegram.TelegramError as error:
        logger.error(f'Не удалось отправить сообщение {error}')
        raise telegram.TelegramError


def get_api_answer(current_timestamp):
    """Запрос к API."""
    logger.info('Запущена функция "get_api_answer"')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            logger.error('Ошибка при запросе к основному API')
            raise exceptions.APIError
        else:
            try:
                return response.json()
            except JSONDecodeError:
                logger.error('Не удалось преобразовать из JSON в dict')
                raise JSONDecodeError

    except requests.exceptions.Timeout:
        logger.error('Время ожидания превышено')
        raise requests.exceptions.Timeout

    except requests.exceptions.TooManyRedirects:
        logger.error('Превышего количество редиректов')
        raise requests.exceptions.TooManyRedirects

    except requests.exceptions.HTTPError as error:
        logger.error(f'Api не доступен {error}')
        raise exceptions.APIError

    except requests.exceptions.RequestException as e:
        logger.error(f'Проблека можключения {e}')
        raise requests.exceptions.RequestException


def check_response(response):
    """Проверка полученного ответа от API."""
    logger.info('Запущена функция "check_response"')
    if not isinstance(response, dict):
        logger.error('Тип данных не dict')
        raise TypeError('Тип данных не dict')
    if 'homeworks' not in response:
        logger.error('Отсутствие ожидаемых ключей в ответе API')
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    if not isinstance(response['homeworks'], list):
        logger.error('Под ключом `homeworks` ДР приходят не в виде списка')
        raise TypeError('Тип данных dict')
    homeworks = response['homeworks']
    if len('homeworks') == 0:
        logger.error('Список проверяемых работ пуст!')
        raise IndexError('Список проверяемых работ пуст!')
    return homeworks


def parse_status(homework):
    """Получение статуса."""
    logger.info('Запущена функция "parse_status"')
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if homework_status not in HOMEWORK_STATUSES:
            logger.error('Невозможно получить необходимое содержимое')
            raise KeyError
    except KeyError:
        logger.error('Невозможно получить необходимое содержимое')
        raise KeyError('Невозможно получить необходимое содержимое')
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    logger.info('Запущена функция "check_tokens"')
    tokens = ("PRACTICUM_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")

    for name in tokens:
        if not globals()[name]:
            logger.critical(f"Не задано значение для {name}")
            return False

    return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            """Не пойму как устранить эту проблему. Но нужно ли?
            У меня прописано исключение IndexError. Тестировал.
            Отправлял пустой список и он не рушил программу,
            а вызывал исключение."""
            message = parse_status(homework)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
