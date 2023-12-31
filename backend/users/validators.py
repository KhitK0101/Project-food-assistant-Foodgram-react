import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    invalid_symbols = ''.join(
        set(re.sub(settings.USERNAME_SYM, '', username))
    )
    if invalid_symbols:
        raise ValidationError(
            settings.NOT_ALLOWED_CHAR_NAME.format(
                chars=invalid_symbols, username=username))
    if username == 'me':
        raise ValidationError(
            settings.NOT_ALLOWED_ME.format(username=username)
        )
    return username
