from celery import task
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)


@task.task()
def fanout_love_feedly(feedly, user, following_group, operation):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    logger.info(u'fanning out for user %s', user.username)
    feeds = feedly._fanout_task(user, following_group, operation)
    return feeds
