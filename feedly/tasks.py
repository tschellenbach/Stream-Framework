from celery import task
from feedly.activity import Activity, AggregatedActivity


@task.task()
def fanout_operation(feed_manager, feed_classes, user_ids, operation, *args, **kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    feed_manager._fanout_task(
        user_ids, feed_classes, operation, *args, **kwargs)
    return "%d user_ids, %r, %r (%r)" % (len(user_ids), feed_classes, operation, (args, kwargs))


@task.task()
def follow_many(feed_manager, user_id, target_ids, follow_limit):
    feeds = feed_manager.get_feeds(user_id).values()
    target_feeds = map(feed_manager.get_user_feed, target_ids)

    activities = []
    for target_feed in target_feeds:
        activities += target_feed[:follow_limit]
    for feed in feeds:
        with feed.get_timeline_batch_interface() as batch_interface:
            feed.add_many(activities, batch_interface=batch_interface)


@task.task()
def unfollow_many(feed_manager, user_id, source_ids):
    for feed in feed_manager.get_feeds(user_id).values():
        activities = []
        feed.trim()
        for item in feed[:]:
            if isinstance(item, Activity):
                if item.actor_id in source_ids:
                    activities.append(item)
            elif isinstance(item, AggregatedActivity):
                activities.extend(
                    [activity for activity in item.activities if activity.actor_id in source_ids])

        if activities:
            feed.remove_many(activities)
