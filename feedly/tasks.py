from celery import task
import logging

logger = logging.getLogger(__name__)


@task.task(queue_name='feedly_fanout_love', routing_key='feedly.fanout_love')
def fanout_love(feedly, user, following_group, operation, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    logger.info(u'fanning out for user %s', user.username)
    feeds = feedly._fanout_task(
        user, following_group, operation, *args, **kwargs)
    
#backward compatibility
fanout_love_feedly = fanout_love


@task.task(queue_name='feedly_follow_many')
def follow_many(feedly, user_id, follower_user_ids):
    '''
    Simple task wrapper for follow_many
    Just making sure code is where you expect it :)
    '''
    logger.info(u'following many for user id %s', user_id)
    feed = feedly._follow_many_task(user_id, follower_user_ids)


@task.task(queue_name='feedly_notifications')
def notification_add_love(love):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._add_love(love)


@task.task(queue_name='feedly_notifications')
def notification_follow(follow):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._follow(follow)


@task.task(queue_name='feedly_notifications')
def notification_add_to_list(list_item):
    from feedly.feed_managers.notification_feedly import NotificationFeedly
    feedly = NotificationFeedly()
    feedly._add_to_list(list_item)
