import re
import base64
from datetime import date, datetime


def read_metrics(values, metrics):
    '''
    Convert the input value to the metric
    If return None, the row must be ignored !
    '''
    if not hasattr(read_metrics, 'prev_row'):
        read_metrics.prev_row = None

    converted_values = []
    for value, metric in zip(values, metrics):
        if value is None:
            return None

        if metric.startswith('python_eval'):
            value = _python_eval(values, read_metrics.prev_row, metric)

        else:
            if '_' + metric not in globals() or metric.startswith('_'):
                raise ValueError('Wrong metric [%s]' % metric)

            method = globals()['_' + metric]
            value = method(value)

        converted_values.append(value)

    read_metrics.prev_row = values

    return converted_values


def _python_eval(row, prev_row, metric):
    # Todo: check if it's safe...
    python_code = metric[12:-1]
    python_code = python_code.replace('__', '')
    return eval(python_code, {}, {'row': row, 'prev_row': prev_row})


def _b64_encoded(value):
    max_len = -1
    b64_word = ''

    for word in re.findall(r'[a-zA-Z0-9\+\/]{5,}={0,3}', value):
        try:
            decoded_bytes = base64.b64decode(word)
            if decoded_bytes.decode('ascii').encode('ascii') != decoded_bytes:
                continue

        except Exception:
            continue

        if base64.b64encode(decoded_bytes) == word.encode('ascii'):
            if len(decoded_bytes) > max_len:
                max_len = len(decoded_bytes)
                b64_word = word

    return b64_word


def _b64_decoded(value):
    encoded = _b64_encoded(value)

    return base64.b64decode(encoded) if encoded else None


def _b64_encoded_len(value):
    encoded = _b64_encoded(value)

    return len(encoded) if encoded else 0


def _str(value):
    return str(value)


def _int(value):
    if isinstance(value, str) and not value.isnumeric():
        return None

    return int(value)


def _float(value):
    if isinstance(value, str) and re.match(r'^\d+?\.\d+?$', value) is None:
        return None

    return float(value)


def _hour(value):
    if isinstance(value, date):
        return date.hour()

    elif isinstance(value, int):
        return datetime.fromtimestamp(value).hour

    elif isinstance(value, float):
        value = int(value / 1000)
        return datetime.fromtimestamp(value).hour

    return None
