from celery import shared_task
from stream_framework.activity import Activity, AggregatedActivity


@shared_task
def fanout_operation(feed_manager, feed_class, user_ids, operation, operation_kwargs):
    '''
    Simple task wrapper for _fanout task
    Just making sure code is where you expect it :)
    '''
    feed_manager.fanout(user_ids, feed_class, operation, operation_kwargs)
    return "%d user_ids, %r, %r (%r)" % (len(user_ids), feed_class, operation, operation_kwargs)


@shared_task
def fanout_operation_hi_priority(feed_manager, feed_class, user_ids, operation, operation_kwargs):
    return fanout_operation(feed_manager, feed_class, user_ids, operation, operation_kwargs)


@shared_task
def fanout_operation_low_priority(feed_manager, feed_class, user_ids, operation, operation_kwargs):
    return fanout_operation(feed_manager, feed_class, user_ids, operation, operation_kwargs)


@shared_task
def follow_many(feed_manager, user_id, target_ids, follow_limit):
    feeds = feed_manager.get_feeds(user_id).values()
    target_feeds = map(feed_manager.get_user_feed, target_ids)

    activities = []
    for target_feed in target_feeds:
        activities += target_feed[:follow_limit]

    if activities:
        for feed in feeds:
            with feed.get_timeline_batch_interface() as batch_interface:
                feed.add_many(activities, batch_interface=batch_interface)


@shared_task
def unfollow_many(feed_manager, user_id, source_ids):
    for feed in feed_manager.get_feeds(user_id).values():
        activities = []
        feed.trim()
        for item in feed[:feed.max_length]:
            if isinstance(item, Activity):
                if item.actor_id in source_ids:
                    activities.append(item)
            elif isinstance(item, AggregatedActivity):
                activities.extend(
                    [activity for activity in item.activities if activity.actor_id in source_ids])

        if activities:
            feed.remove_many(activities)
