Stream Framework
----------------

[![Build Status](https://travis-ci.org/tschellenbach/Stream-Framework.png?branch=master)](https://travis-ci.org/tschellenbach/Stream-Framework)
[![PyPI version](https://badge.fury.io/py/stream-framework.svg)](http://badge.fury.io/py/stream-framework)


## Activity Streams & Newsfeeds ##


<p align="center">
  <img src="https://dvqg2dogggmn6.cloudfront.net/images/mood-home.png" alt="Examples of what you can build" title="What you can build"/>
</p>

Stream Framework is a python library which allows you to build activity streams & newsfeeds using Cassandra and/or Redis. If you're not using python have a look at [Stream] (https://getstream.io/), which supports Node, Ruby, PHP, Python, Go, Scala,  Java and REST.

Examples of what you can build are:

* Activity streams such as seen on Github
* A Twitter style newsfeed
* A feed like Instagram/ Pinterest
* Facebook style newsfeeds
* A notification system

(Feeds are also commonly called: Activity Streams, activity feeds, news streams.)



[fashiolista]: http://www.fashiolista.com/
[stream]: http://getstream.io/
[blog]: http://blog.getstream.io/post/98149880113/introducing-the-stream-framework
[stream_js]: https://github.com/tschellenbach/stream-js
[stream_python]: https://github.com/tschellenbach/stream-python
[stream_php]: https://github.com/tbarbugli/stream-php
[stream_ruby]: https://github.com/tbarbugli/stream-ruby
[fashiolista_flat]: http://www.fashiolista.com/feed/?feed_type=F
[fashiolista_aggregated]: http://www.fashiolista.com/feed/?feed_type=A
[fashiolista_notification]: http://www.fashiolista.com/my_style/notification/
[example_app_link]: https://github.com/tbarbugli/stream_framework_example



## Stream ##

<a href="https://getstream.io/"><img src="http://dvqg2dogggmn6.cloudfront.net/images/getstream-dot-io-logo-light.png" alt="Build scalable newsfeeds and activity streams using getstream.io" title="Build scalable newsfeeds and activity streams using getstream.io" width="300px"/></a>

Stream Framework's authors also offer a web service for building scalable newsfeeds & activity streams at [getstream.io] [stream]
It allows you to create your feeds by talking to a beautiful and easy to use REST API. There are clients available for Node, Ruby, PHP, Python, Go, Scala and Java. The [get started](https://getstream.io/get_started/#intro) explains the API & concept in a few clicks. Its a lot easier to use, free up to 3 million feed updates and saves you the hassle of maintaining Cassandra, Redis, Faye, RabbitMQ and Celery workers.

## Stream Framework ##


**Installation**

Installation through pip is recommended::

    $ pip install stream-framework

Or you can choose to specify your dependencies (you can add this format to a requirements file)

```
$ pip install stream-framework[cassandra2]
```

```
$ pip install stream-framework[cassandra3]
```

```
$ pip install stream-framework[redis]
```

**Authors & Contributors**

 * Thierry Schellenbach (thierry at getstream.io)
 * Tommaso Barbugli (tommaso at getstream.io)
 * Anislav Atanasov
 * Guyon Morée

**Resources**

 * [Documentation] 
 * [Bug Tracker] 
 * [Code] 
 * [Travis CI] 
 * [Stackoverflow]
 
**Example application**

We've included a [Pinterest like example application] [example_app_link] based on Stream Framework. 

**Tutorials**

 * [Pinterest style feed example app] [mellowmorning_example]
 

[mellowmorning_example]: http://www.mellowmorning.com/2013/10/18/scalable-pinterest-tutorial-feedly-redis/
[Documentation]: https://stream-framework.readthedocs.org/
[Bug Tracker]: https://github.com/tschellenbach/Stream-Framework/issues
[Code]: http://github.com/tschellenbach/Stream-Framework
[Travis CI]: http://travis-ci.org/tschellenbach/Stream-Framework/
[Stackoverflow]: http://stackoverflow.com/questions/tagged/stream-framework

## Using Stream Framework ##

This quick example will show you how to publish a Pin to all your followers. So lets create
an activity for the item you just pinned.

```python
from stream_framework.activity import Activity


def create_activity(pin):
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
First of all we want to insert it into your personal feed, and then into your followers' feeds.
Lets start by defining these feeds.

```python

from stream_framework.feeds.redis import RedisFeed


class UserPinFeed(PinFeed):
    key_format = 'feed:user:%(user_id)s'


class PinFeed(RedisFeed):
    key_format = 'feed:normal:%(user_id)s'
```

Writing to these feeds is very simple. For instance to write to the feed of user 13 one would do

```python

feed = UserPinFeed(13)
feed.add(activity)
```

But we don't want to publish to just one users feed. We want to publish to the feeds of all users which follow you.
This action is called a fanout and is abstracted away in the manager class.
We need to subclass the Manager class and tell it how we can figure out which user follow us.

```python

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
```

Now that the manager class is setup broadcasting a pin becomes as easy as

```python
manager.add_pin(pin)
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
    feed = manager.get_feeds(request.user.id)['normal']
    activities = list(feed[:25])
    context['activities'] = activities
    response = render_to_response('core/feed.html', context)
    return response

```

This example only briefly covered how Stream Framework works.
The full explanation can be found on read the docs.


## Features ##

Stream Framework uses celery and Redis/Cassandra to build a system with heavy writes and extremely light reads.
It features:

  - Asynchronous tasks (All the heavy lifting happens in the background, your users don't wait for it)
  - Reusable components (You will need to make tradeoffs based on your use cases, Stream Framework doesnt get in your way)
  - Full Cassandra and Redis support
  - The Cassandra storage uses the new CQL3 and Python-Driver packages, which give you access to the latest Cassandra features.
  - Build for the extremely performant Cassandra 2.1. 2.2 and 3.3 also pass the test suite, but no production experience.


## Background Articles ##

A lot has been written about the best approaches to building feed based systems.
Here's a collection on some of the talks:

[Twitter 2013] [twitter_2013]
Redis based, database fallback, very similar to Fashiolista's old approach.

[twitter_2013]: http://highscalability.com/blog/2013/7/8/the-architecture-twitter-uses-to-deal-with-150m-active-users.html

[Etsy feed scaling] [etsy]
(Gearman, separate scoring and aggregation steps, rollups - aggregation part two)

[etsy]: http://www.slideshare.net/danmckinley/etsy-activity-feeds-architecture/

[linkedin]: https://engineering.linkedin.com/blog/2016/03/followfeed--linkedin-s-feed-made-faster-and-smarter
[LinkedIn ranked feeds] [linkedin]

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

[yahoo]: http://jeffterrace.com/docs/feeding-frenzy-sigmod10-web.pdf

[Twitter’s approach] [twitter]

[twitter]: http://www.slideshare.net/nkallen/q-con-3770885

[Cassandra at Instagram] [instagram]

[instagram]: http://planetcassandra.org/blog/post/instagram-making-the-switch-to-cassandra-from-redis-75-instasavings

[Relevancy at Etsy][etsy_relevancy]
[etsy_relevancy]: http://mimno.infosci.cornell.edu/info6150/readings/p1640-hu.pdf

[Zite architecture overview][zite]
[zite]: http://blog.zite.com/2012/01/11/zite-under-the-hood/

[Ranked feeds with ES][es]
[es]: https://speakerdeck.com/viadeoteam/a-personalized-news-feed

[Riak at Xing - by Dr. Stefan Kaes & Sebastian Röbke][xing]
[xing]: https://www.youtube.com/watch?v=38yKu5HR-tM

[Riak and Scala at Yammer][yammer]
[yammer]: http://basho.com/posts/business/riak-and-scala-at-yammer/


