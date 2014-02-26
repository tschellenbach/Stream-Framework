SECRET_KEY = '123456789'

FEEDLY_DEFAULT_KEYSPACE = 'test'

FEEDLY_CASSANDRA_HOSTS = [
	'127.0.0.1', '127.0.0.2', '127.0.0.3'
]

CELERY_ALWAYS_EAGER = True

import djcelery
djcelery.setup_loader()
