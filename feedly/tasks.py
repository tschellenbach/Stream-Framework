from celery import task
import logging

logger = logging.getLogger(__name__)


@task.task()
def fanout_love(feedly, user, following_group, operation, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    logger.info(u'fanning out for user %s', user.username)
    feeds = feedly._fanout_task(
        user, following_group, operation, *args, **kwargs)


@task.task()
def follow_many(feedly, user_id, follower_user_ids):
    '''
    Simple task wrapper for follow_many
    Just making sure code is where you expect it :)
    '''
    logger.info(u'following many for user id %s', user_id)
    feed = feedly._follow_many_task(user_id, follower_user_ids)


@task.task()
def notification_add_love(love):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._add_love(love)


@task.task()
def notification_follow(follow):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._follow(follow)


@task.task()
def notification_add_to_list(list_item):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._add_to_list(list_item)
