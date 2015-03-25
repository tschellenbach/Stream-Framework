Stream Framework (previously Feedly)
------------------------------------

|Build Status|

**Note**

This project was previously named Feedly. As requested by feedly.com we
have now renamed the project to Stream Framework. You can find more
details about the name change on the
`blog <http://blog.getstream.io/post/98149880113/introducing-the-stream-framework>`__.

What can you build?
-------------------

Stream Framework allows you to build newsfeed and notification systems
using Cassandra and/or Redis. Examples of what you can build are the
Facebook newsfeed, your Twitter stream or your Pinterest following page.
We've built Feedly for `Fashiolista <http://www.fashiolista.com/>`__
where it powers the `flat
feed <http://www.fashiolista.com/feed/?feed_type=F>`__, `aggregated
feed <http://www.fashiolista.com/feed/?feed_type=A>`__ and the
`notification
system <http://www.fashiolista.com/my_style/notification/>`__. (Feeds
are also commonly called: Activity Streams, activity feeds, news
streams.)

To quickly make you acquainted with Stream Framework, we've created a
Pinterest like example application, you can find it
`here <https://github.com/tbarbugli/stream_framework_example>`__

GetStream.io
------------

Stream Framework's authors also offer a Saas solution for building feed
systems at `getstream.io <http://getstream.io/>`__ The hosted service is
highly optimized and allows you start building your application
immediatly. It saves you the hastle of maintaining Cassandra, Redis,
Faye, RabbitMQ and Celery workers. Clients are available for
`Node <https://github.com/GetStream/stream-js>`__,
`Ruby <https://github.com/GetStream/stream-ruby>`__,
`Python <https://github.com/GetStream/stream-python>`__,
`Java <https://github.com/GetStream/stream-java>`__ and
`PHP <https://github.com/GetStream/stream-php>`__

Consultancy
-----------

For Stream Framework and GetStream.io consultancy please contact thierry
at getstream.io

**Authors**

-  Thierry Schellenbach (thierry at getstream.io)
-  Tommaso Barbugli (tommaso at getstream.io)
-  Guyon Morée

**Resources**

-  `Documentation <https://stream-framework.readthedocs.org/>`__
-  `Bug Tracker <http://github.com/tschellenbach/Feedly/issues>`__
-  `Code <http://github.com/tschellenbach/Stream-Framework>`__
-  `Mailing List <https://groups.google.com/group/feedly-python>`__
-  `IRC <irc://irc.freenode.net/feedly-python>`__ (irc.freenode.net,
   #feedly-python)
-  `Travis CI <http://travis-ci.org/tschellenbach/Stream-Framework/>`__

**Tutorials**

-  `Pinterest style feed example
   app <http://www.mellowmorning.com/2013/10/18/scalable-pinterest-tutorial-feedly-redis/>`__

Using Stream Framework
----------------------

This quick example will show you how to publish a Pin to all your
followers. So lets create an activity for the item you just pinned.

.. code:: python

    def create_activity(pin):
        from stream_framework.activity import Activity
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

    from stream_framework.feeds.redis import RedisFeed


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
fanout and is abstracted away in the manager class. We need to subclass
the Manager class and tell it how we can figure out which user follow
us.

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

Now that the manager class is setup broadcasting a pin becomes as easy
as

.. code:: python

    manager.add_pin(pin)

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
        feed = manager.get_feeds(request.user.id)['normal']
        activities = list(feed[:25])
        context['activities'] = activities
        response = render_to_response('core/feed.html', context)
        return response

This example only briefly covered how Stream Framework works. The full
explanation can be found on read the docs.

Features
--------

Stream Framework uses celery and Redis/Cassandra to build a system with
heavy writes and extremely light reads. It features:

-  Asynchronous tasks (All the heavy lifting happens in the background,
   your users don't wait for it)
-  Reusable components (You will need to make tradeoffs based on your
   use cases, Stream Framework doesnt get in your way)
-  Full Cassandra and Redis support
-  The Cassandra storage uses the new CQL3 and Python-Driver packages,
   which give you access to the latest Cassandra features.
-  Built for the extremely performant Cassandra 2.0

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

`Django project with good naming
conventions <http://justquick.github.com/django-activity-stream/>`__

`Activity stream
specification <http://activitystrea.ms/specs/atom/1.0/>`__

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

.. |Build Status| image:: https://travis-ci.org/tschellenbach/Stream-Framework.png?branch=master
   :target: https://travis-ci.org/tschellenbach/Stream-Framework
