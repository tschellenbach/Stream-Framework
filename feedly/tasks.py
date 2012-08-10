from celery import task
import logging

logger = logging.getLogger(__name__)


@task.task()
def fanout_love_feedly(feedly, user, following_group, operation, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    logger.info(u'fanning out for user %s', user.username)
    feeds = feedly._fanout_task(user, following_group, operation, *args, **kwargs)


@task.task()
def follow_many(feedly, user_id, follower_user_ids):
    '''
    Simple task wrapper for follow_many
    Just making sure code is where you expect it :)
    '''
    logger.info(u'following many for user id %s', user_id)
    feed = feedly._follow_many_task(user_id, follower_user_ids)
