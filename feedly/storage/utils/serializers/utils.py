from feedly.exceptions import SerializationException


def check_reserved(value, reserved_characters):
    if any([reserved in value for reserved in reserved_characters]):
        raise SerializationException(
            'encountered reserved character %s in %s' % (reserved, value))
