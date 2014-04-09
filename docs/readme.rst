Feedly
------

|Build Status|

**Note**

The Feedly open source project is in no way related to feedly.com. To
avoid confusion we are considering renaming the 1.0 release of the
project.

What can you build?
-------------------

Feedly allows you to build newsfeed and notification systems using
Cassandra and/or Redis. Examples of what you can build are the Facebook
newsfeed, your Twitter stream or your Pinterest following page. We've
built Feedly for `Fashiolista <http://www.fashiolista.com/>`__ where it
powers the `flat feed <http://www.fashiolista.com/feed/?feed_type=F>`__,
`aggregated feed <http://www.fashiolista.com/feed/?feed_type=A>`__ and
the `notification
system <http://www.fashiolista.com/my_style/notification/>`__. (Feeds
are also commonly called: Activity Streams, activity feeds, news
streams.)

[readme\_developing]:
https://github.com/tschellenbach/Feedly/blob/master/README.md#developing-feedly
To quickly make you acquainted with Feedly, we've created a Pinterest
like example application, you can find it
`here <https://github.com/tbarbugli/feedly_pin/>`__

**Authors**

-  Thierry Schellenbach
-  Tommaso Barbugli
-  Guyon Morée

**Resources**

-  `Documentation <https://feedly.readthedocs.org/>`__
-  `Bug Tracker <http://github.com/tschellenbach/Feedly/issues>`__
-  `Code <http://github.com/tschellenbach/Feedly>`__
-  `Mailing List <https://groups.google.com/group/feedly-python>`__
-  `IRC <irc://irc.freenode.net/feedly-python>`__ (irc.freenode.net,
   #feedly-python)
-  `Travis CI <http://travis-ci.org/tschellenbach/Feedly/>`__

Using Feedly
------------

This quick example will show you how to publish a Pin to all your
followers. So lets create an activity for the item you just pinned.

.. code:: python

    def create_activity(pin):
        from feedly.activity import Activity
        activity = Activity(
            pin.user_id,
            PinVerb,
            pin.id,
            pin.influencer_id,
            time=make_naive(pin.created_at, pytz.utc),
            extra_context=dict(item_id=pin.item_id)
        )
        return activity

Next up we want to start publishing this activity on several feeds.
First of we want to insert it into your personal feed, and secondly into
the feeds of all your followers. Lets start first by defining these
feeds.

.. code:: python

    # setting up the feeds

    class PinFeed(RedisFeed):
        key_format = 'feed:normal:%(user_id)s'

    class UserPinFeed(PinFeed):
        key_format = 'feed:user:%(user_id)s'

Writing to these feeds is very simple. For instance to write to the feed
of user 13 one would do

.. code:: python


    feed = UserPinFeed(13)
    feed.add(activity)

But we don't want to publish to just one users feed. We want to publish
to the feeds of all users which follow you. This action is called a
fanout and is abstracted away in the Feedly manager class. We need to
subclass the Feedly class and tell it how we can figure out which user
follow us.

.. code:: python


    class PinFeedly(Feedly):
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
        
    feedly = PinFeedly()

Now that the feedly class is setup broadcasting a pin becomes as easy as

.. code:: python

    feedly.add_pin(pin)

Calling this method wil insert the pin into your personal feed and into
all the feeds of users which follow you. It does so by spawning many
small tasks via Celery. In Django (or any other framework) you can now
show the users feed.

.. code:: python

    # django example

    @login_required
    def feed(request):
        '''
        Items pinned by the people you follow
        '''
        context = RequestContext(request)
        feed = feedly.get_feeds(request.user.id)['normal']
        activities = list(feed[:25])
        context['activities'] = activities
        response = render_to_response('core/feed.html', context)
        return response

This example only briefly covered how Feedly works. The full explanation
can be found on read the docs.

**Documentation**

[Installing Feedly] [docs\_install] [docs\_install]:
https://feedly.readthedocs.org/en/latest/installation.html [Settings]
[docs\_settings] [docs\_settings]:
https://feedly.readthedocs.org/en/latest/settings.html [Feedly (Feed
manager class) implementation] [docs\_feedly] [docs\_feedly]:
https://feedly.readthedocs.org/en/latest/feedly.feed\_managers.html#module-feedly.feed\_managers.base
[Feed class implementation] [docs\_feed] [docs\_feed]:
https://feedly.readthedocs.org/en/latest/feedly.feeds.html [Choosing the
right storage backend] [docs\_storage\_backend]
[docs\_storage\_backend]:
https://feedly.readthedocs.org/en/latest/choosing\_a\_storage\_backend.html
[Building notification systems] [docs\_notification\_systems]
[docs\_notification\_systems]:
https://feedly.readthedocs.org/en/latest/notification\_systems.html

**Tutorials**

[Pinterest style feed example app] [mellowmorning\_example]
[mellowmorning\_example]:
http://www.mellowmorning.com/2013/10/18/scalable-pinterest-tutorial-feedly-redis/



Background Articles
-------------------

A lot has been written about the best approaches to building feed based
systems. Here's a collection on some of the talks:

`Twitter
2013 <http://highscalability.com/blog/2013/7/8/the-architecture-twitter-uses-to-deal-with-150m-active-users.html>`__
Redis based, database fallback, very similar to Fashiolista's old
approach.

`Etsy feed
scaling <http://www.slideshare.net/danmckinley/etsy-activity-feeds-architecture/>`__
(Gearman, separate scoring and aggregation steps, rollups - aggregation
part two)

`Facebook
history <http://www.infoq.com/presentations/Facebook-Software-Stack>`__

[Django project, with good naming conventions.] [djproject] [djproject]:
http://justquick.github.com/django-activity-stream/
http://activitystrea.ms/specs/atom/1.0/ (actor, verb, object, target)

`Quora post on best
practises <http://www.quora.com/What-are-best-practices-for-building-something-like-a-News-Feed?q=news+feeds>`__

`Quora scaling a social network
feed <http://www.quora.com/What-are-the-scaling-issues-to-keep-in-mind-while-developing-a-social-network-feed>`__

`Redis ruby
example <http://blog.waxman.me/how-to-build-a-fast-news-feed-in-redis>`__

`FriendFeed
approach <http://backchannel.org/blog/friendfeed-schemaless-mysql>`__

`Thoonk setup <http://blog.thoonk.com/>`__

`Yahoo Research
Paper <http://research.yahoo.com/files/sigmod278-silberstein.pdf>`__

`Twitter’s approach <http://www.slideshare.net/nkallen/q-con-3770885>`__

`Cassandra at
Instagram <http://planetcassandra.org/blog/post/instagram-making-the-switch-to-cassandra-from-redis-75-instasavings>`__

.. |Build Status| image:: https://travis-ci.org/tschellenbach/Feedly.png?branch=master
   :target: https://travis-ci.org/tschellenbach/Feedly
