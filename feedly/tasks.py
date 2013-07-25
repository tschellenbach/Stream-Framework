from celery import task


@task.task()
def fanout_operation(feed_manager, feed_classes, user_ids, operation, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    feed_manager._fanout_task(
        user_ids, feed_classes, operation, *args, **kwargs)


@task.task()
def follow_many(feeds, target_feeds, follow_limit):
    # TODO optimize this (eg. use a batch operator!)
    activities = []
    for target_feed in target_feeds:
        activities += target_feed[:follow_limit]
    for feed in feeds:
        feed.add_many(activities)

@task.task()
def unfollow_many(feeds, source_feeds):
    # TODO optimize this (eg. use a batch operator!)
    activities = []
    for source_feed in source_feeds:
        activities += source_feed[:]
    for feed in feeds:
        feed.remove_many(activities)