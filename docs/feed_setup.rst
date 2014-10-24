Feed setup
==========

A feed object contains activities. The example below shows you how to setup
two feeds:

.. code:: python

    # implement your feed with redis as storage

    from stream_framework.feeds.redis import RedisFeed

    class PinFeed(RedisFeed):
        key_format = 'feed:normal:%(user_id)s'

    class UserPinFeed(PinFeed):
        key_format = 'feed:user:%(user_id)s'
        
        
Next up we need to hook up the Feeds to your Manager class.   
The Manager class knows how to fanout new activities to the feeds of all your followers.  
        
.. code:: python

    from stream_framework.feed_managers.base import Manager


    class PinManager(Manager):
        feed_classes = dict(
            normal=PinFeed,
        )
        user_feed_class = UserPinFeed
        
        def add_pin(self, pin):
            activity = pin.create_activity()
            # add user activity adds it to the user feed, and starts the fanout
            self.add_user_activity(pin.user_id, activity)

        def get_user_follower_ids(self, user_id):
            ids = Follow.objects.filter(target=user_id).values_list('user_id', flat=True)
            return {FanoutPriority.HIGH:ids}
        
    manager = PinManager()
