from celery import task
import logging

logger = logging.getLogger(__name__)


@task.task()
def fanout_operation(feed_manager, feeds, operation, max_length=None, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    feed_manager._fanout_task(
        feeds, operation, max_length=max_length, *args, **kwargs)


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
