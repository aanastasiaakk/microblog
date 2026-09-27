import time
import requests
from flask import current_app
from flask_babel import _

# РЕЗІЛЬЄНТНІСТЬ (Завд.2 ЛР2): параметри Retry винесено в константи
# і свідомо обмежено, щоб уникнути retry storm:
#   - MAX_RETRIES = 3      -> не більше 3 спроб на запит користувача
#   - REQUEST_TIMEOUT = 2s -> кожна спроба чекає не довше 2 секунд
#   - експоненційний backoff (0.5s, 1s) -> паузи між спробами
#     наростають, а не б'ють у вже перевантажену залежність одразу
#     й синхронно знову (саме так виникає retry storm).
MAX_RETRIES = 3
REQUEST_TIMEOUT = 2
RETRY_BACKOFF_BASE = 0.5


def translate(text, source_language, dest_language):
    if 'MS_TRANSLATOR_KEY' not in current_app.config or \
            not current_app.config['MS_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    auth = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'westus'
    }
    url = current_app.config['TRANSLATOR_API_URL'] + \
        '?api-version=3.0&from={}&to={}'.format(
            source_language, dest_language)
    payload = [{'Text': text}]

    last_error = 'unknown error'
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(url, headers=auth, json=payload,
                               timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()[0]['translations'][0]['text']
            last_error = 'HTTP {}'.format(r.status_code)
        except requests.exceptions.Timeout:
            last_error = 'timeout'
        except requests.exceptions.ConnectionError:
            last_error = 'connection error'

        current_app.logger.warning(
            'Translate API attempt %d/%d failed: %s',
            attempt, MAX_RETRIES, last_error)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))

    # FALLBACK: усі спроби вичерпано -> Graceful Degradation.
    # Сервіс не падає з необробленим винятком (500), а повертає
    # користувачу безпечну деградовану відповідь + діагностичний
    # запис у логах для подальшого аналізу.
    current_app.logger.error(
        'Translate API unavailable after %d attempts (%s). '
        'Returning fallback response.', MAX_RETRIES, last_error)
    fallback_note = _('translation unavailable')
    return '{} ({})'.format(text, fallback_note)
