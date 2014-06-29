Feedly
------

[![Build Status](https://travis-ci.org/tschellenbach/Feedly.png?branch=master)](https://travis-ci.org/tschellenbach/Feedly)

**Note**

The Feedly open source project is in no way related to feedly.com. To avoid confusion we are considering renaming the 1.0 release of the project.


## What can you build? ##

Feedly allows you to build newsfeed and notification systems using Cassandra and/or Redis.
Examples of what you can build are the Facebook newsfeed, your Twitter stream or your Pinterest following page.
We've built Feedly for [Fashiolista] [fashiolista] where it powers the [flat feed] [fashiolista_flat], [aggregated feed] [fashiolista_aggregated] and the [notification system] [fashiolista_notification].
(Feeds are also commonly called: Activity Streams, activity feeds, news streams.)

[fashiolista]: http://www.fashiolista.com/
[stream]: http://getstream.io/
[stream_js]: https://github.com/tschellenbach/stream-js
[stream_python]: https://github.com/tschellenbach/stream-python
[stream_php]: https://github.com/tbarbugli/stream-php
[stream_ruby]: https://github.com/tbarbugli/stream-ruby
[fashiolista_flat]: http://www.fashiolista.com/feed/?feed_type=F
[fashiolista_aggregated]: http://www.fashiolista.com/feed/?feed_type=A
[fashiolista_notification]: http://www.fashiolista.com/my_style/notification/
[example_app_link]: https://github.com/tbarbugli/feedly_pin/

To quickly make you acquainted with Feedly, we've created a Pinterest like example application, you can find it [here] [example_app_link]

## GetStream.io - Promotion ##

Feedly's authors also offer a Saas solution for building feed systems at [getstream.io] [stream]
The hosted service is highly optimized and allows you start building your application immediatly.
It saves you the hastle of maintaining Cassandra, Redis, Faye, RabbitMQ and Celery workers.
Clients are available for [Node] [stream_js], [Ruby] [stream_ruby], [Python] [stream_python] and [PHP] [stream_php]


**Authors**

 * Thierry Schellenbach
 * Tommaso Barbugli
 * Guyon Morée


**Resources**

 * [Documentation] 
 * [Bug Tracker] 
 * [Code] 
 * [Mailing List] 
 * [IRC]  (irc.freenode.net, #feedly-python) 
 * [Travis CI] 
 

**Tutorials**

 * [Pinterest style feed example app] [mellowmorning_example]
 

[mellowmorning_example]: http://www.mellowmorning.com/2013/10/18/scalable-pinterest-tutorial-feedly-redis/
[Documentation]: https://feedly.readthedocs.org/
[Bug Tracker]: http://github.com/tschellenbach/Feedly/issues
[Code]: http://github.com/tschellenbach/Feedly
[Mailing List]: https://groups.google.com/group/feedly-python
[IRC]: irc://irc.freenode.net/feedly-python
[Travis CI]: http://travis-ci.org/tschellenbach/Feedly/


## Using Feedly ##

This quick example will show you how to publish a Pin to all your followers. So lets create
an activity for the item you just pinned.

```python
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
```

Next up we want to start publishing this activity on several feeds.
First of we want to insert it into your personal feed, and secondly into the feeds of all your followers.
Lets start first by defining these feeds.

```python
# setting up the feeds

class PinFeed(RedisFeed):
    key_format = 'feed:normal:%(user_id)s'

class UserPinFeed(PinFeed):
    key_format = 'feed:user:%(user_id)s'
```

Writing to these feeds is very simple. For instance to write to the feed of user 13 one would do

```python

feed = UserPinFeed(13)
feed.add(activity)
```

But we don't want to publish to just one users feed. We want to publish to the feeds of all users which follow you.
This action is called a fanout and is abstracted away in the Feedly manager class.
We need to subclass the Feedly class and tell it how we can figure out which user follow us.

```python

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
```

Now that the feedly class is setup broadcasting a pin becomes as easy as

```python
feedly.add_pin(pin)
```

Calling this method wil insert the pin into your personal feed and into all the feeds of users which follow you.
It does so by spawning many small tasks via Celery. In Django (or any other framework) you can now show the users feed.

```python
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

```

This example only briefly covered how Feedly works.
The full explanation can be found on read the docs.


## Features ##

Feedly uses celery and Redis/Cassandra to build a system with heavy writes and extremely light reads.
It features:

  - Asynchronous tasks (All the heavy lifting happens in the background, your users don't wait for it)
  - Reusable components (You will need to make tradeoffs based on your use cases, Feedly doesnt get in your way)
  - Full Cassandra and Redis support
  - The Cassandra storage uses the new CQL3 and Python-Driver packages, which give you access to the latest Cassandra features.
  - Built for the extremely performant Cassandra 2.0


## Background Articles ##

A lot has been written about the best approaches to building feed based systems.
Here's a collection on some of the talks:

[Twitter 2013] [twitter_2013]
Redis based, database fallback, very similar to Fashiolista's old approach.

[twitter_2013]: http://highscalability.com/blog/2013/7/8/the-architecture-twitter-uses-to-deal-with-150m-active-users.html

[Etsy feed scaling] [etsy]
(Gearman, separate scoring and aggregation steps, rollups - aggregation part two)

[etsy]: http://www.slideshare.net/danmckinley/etsy-activity-feeds-architecture/


[facebook]: http://www.infoq.com/presentations/Facebook-Software-Stack
[Facebook history] [facebook]


[djproject]: http://justquick.github.com/django-activity-stream/
[Django project with good naming conventions] [djproject]


[activity_stream]: http://activitystrea.ms/specs/atom/1.0/
[Activity stream specification] [activity_stream]

[Quora post on best practises] [quora]

[quora]: http://www.quora.com/What-are-best-practices-for-building-something-like-a-News-Feed?q=news+feeds

[Quora scaling a social network feed] [quora2]

[quora2]: http://www.quora.com/What-are-the-scaling-issues-to-keep-in-mind-while-developing-a-social-network-feed

[Redis ruby example] [redisruby]

[redisruby]: http://blog.waxman.me/how-to-build-a-fast-news-feed-in-redis

[FriendFeed approach] [friendfeed]

[friendfeed]: http://backchannel.org/blog/friendfeed-schemaless-mysql

[Thoonk setup] [thoonk]

[thoonk]: http://blog.thoonk.com/

[Yahoo Research Paper] [yahoo]

[yahoo]: http://research.yahoo.com/files/sigmod278-silberstein.pdf

[Twitter’s approach] [twitter]

[twitter]: http://www.slideshare.net/nkallen/q-con-3770885

[Cassandra at Instagram] [instagram]

[instagram]: http://planetcassandra.org/blog/post/instagram-making-the-switch-to-cassandra-from-redis-75-instasavings



