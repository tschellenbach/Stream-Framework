from stream_framework.exceptions import SerializationException


def check_reserved(value, reserved_characters):
	for reserved in reserved_characters:
		if reserved in value:
			raise SerializationException(
            	'encountered reserved character %s in %s' % (reserved, value))
