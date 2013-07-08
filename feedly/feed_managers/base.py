

class Feedly(object):

    '''
    A feedly class abstracts away the logic for fanning out to your followers
    '''
    def __init__(self, feed_class, timeline_storage_options={}, activity_storage_options={}):
        '''
        This manager is built specifically for the love feed
        '''
        self.feed_class = feed_class
        self.timeline_storage_options = timeline_storage_options
        self.activity_storage_options = activity_storage_options

    def get_feed(self, user_id):
        return self.feed_class(
            user_id,
            'feed_%(user_id)s',
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def get_user_feed(self, user_id):
        return self.user_feed_class(
            user_id,
            'user_%(user_id)s_feed',
            timeline_storage_options=self.timeline_storage_options,
            activity_storage_options=self.activity_storage_options
        )

    def _fanout(self, user, operation, *args, **kwargs):
        '''
        Generic functionality for running an operation on all of your
        follower's feeds

        It takes the following ids and distributes them per FANOUT_CHUNKS
        '''
        follower_groups = self.get_follower_groups(user)
        feeds = []
        for follower_group in follower_groups:
            # now, for these items pipeline/thread away via an async task
            from feedly.tasks import fanout_love
            fanout_love(
                self, user, follower_group, operation, *args, **kwargs
            )
        return feeds

    def _fanout_task(self, user, following_group, operation, max_length=None, *args, **kwargs):
        '''
        This bit of the fan-out is normally called via an Async task
        this shouldnt do any db queries whatsoever
        '''
        feeds = []

        for following_id in following_group:
            feed = self.get_feed(following_id)
            feeds.append(feed)
            operation(feed, *args, **kwargs)
        return feeds