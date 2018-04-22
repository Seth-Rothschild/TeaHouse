import requests
from weiqi import settings


class RecaptchaError(Exception):
    pass


def validate_recaptcha(response):
    backend = globals()[settings.RECAPTCHA['backend'] + '_validator']
    backend(response)


def dummy_validator(response):
    pass


def google_validator(response):
    res = requests.post('https://www.google.com/recaptcha/api/siteverify', {
        'secret': settings.RECAPTCHA['secret'],
        'response': response,
    })

    data = res.json()

    if not data['success']:
        raise RecaptchaError('reCAPTCHA verification did not return a success')
