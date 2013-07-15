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
def follow_many(feed, target_feeds, follow_limit):
    for target_feed in target_feeds:
        activities = target_feed[:follow_limit]
        activity_ids = [a.serialization_id for a in activities]
        return feed.add_many(activity_ids)
