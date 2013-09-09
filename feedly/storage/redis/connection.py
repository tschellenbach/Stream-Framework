import redis
from feedly import settings

connection_pool = None

def get_redis_connection():
	global connection_pool

	if connection_pool is None:
		connection_pool = setup_redis()

	return redis.StrictRedis(connection_pool=connection_pool)

def setup_redis():
	return redis.ConnectionPool(
		host=settings.FEEDLY_REDIS_CONFIG['host'],
		port=settings.FEEDLY_REDIS_CONFIG['port'],
		db=settings.FEEDLY_REDIS_CONFIG['db']
	)
