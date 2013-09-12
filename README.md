Feedly
------

[![Build Status](https://www.travis-ci.org/tschellenbach/Feedly.png?branch=cassandra)](https://www.travis-ci.org/tschellenbach/Feedly)

[![Coverage Status](https://coveralls.io/repos/tschellenbach/Feedly/badge.png?branch=master&random=1)](https://coveralls.io/r/tschellenbach/Feedly?branch=master)

Feedly allows you to build newsfeed and notification systems using Cassandra and/or Redis.
Examples of what you can build are systems like the Facebook newsfeed, your Twitter stream or your Pinterest following page.

We've built it for [Fashiolista] [fashiolista] where it powers the [flat feed] [fashiolista_flat], [aggregated feed] [fashiolista_aggregated] and the notification system.
[fashiolista]: http://www.fashiolista.com/
[fashiolista_flat]: http://www.fashiolista.com/feed/
[fashiolista_aggregated]: http://www.fashiolista.com/feed/?design=1

To quickly make you acquinted with Feedly, we've included a Pinterest like example application.

**Authors**

* Thierry Schellenbach
* Tommaso Barbugli
* Guyon Morée
* Kuus (Example app design)


**Roadmap**

Feedly is currently used in production at Fashiolista. We are still making rapid changes to this project.
The APIs will only freeze when we reach version 1.0. For version 1.0 we're currently aiming to improve the:

* Documentation and tutorials
* Example application
* Redis, Replacing Nydus with Twemproxy


**What is a feed?**

A feed is a stream of content which is created by people or subjects you follow.
Feeds are also commonly called: Activity Streams, activity feeds, news streams.


**Why is it hard?**

*The first approach*

A first feed solution usually looks something like this:

```sql
SELECT * FROM tweets
JOIN follow ON (follow.target_id = tweet.user_id)
WHERE follow.user_id = 13
```

This works in the beginning, and with a well tuned database will keep on working nicely for quite some time.
However at some point the load becomes too much and this approach falls apart. Unfortunately it's very hard
to split up the tweets in a meaningfull way. You could split it up by date or user, but every query will still hit
many of your shards. Eventually this system collapses, read more about this in [Facebook's presentation] [facebook].

*Push or Push/Pull*
In general there are two similar solutions to this problem.

In the push approach you publish your activity (ie a tweet on twitter) to all of your followers. So basically you create a small list
per user to which you insert the activities created by the people they follow. This involves a huge number of writes, but reads are really fast they can easily be sharded.

For the push/pull approach you implement the push based systems for a subset of your users. At Fashiolista for instance we used to
have a push based approach for active users. For inactive users we only kept a small feed and eventually used a fallback to the database
when we ran out of results.

**Feedly**

Feedly allows you to easily use Cassndra/Redis and Celery (an awesome task broker) to build infinitely scalable feeds.
The high level functionality is located in 4 classes.

  - Activities
  - Feeds
  - Feed managers (Feedly)
  - Aggregators

*Activities* are the blocks of content which are stored in a feed. It follows the nomenclatura from the [activity stream spec] [astream]
[astream]: http://activitystrea.ms/specs/atom/1.0/#activity.summary
Every activity therefor stores at least:

  - Time (the time of the activity)
  - Verb (the action, ie loved, liked, followed)
  - Actor (the user id doing the action)
  - Object (the object the action is related to)
  - Extra context (Used for whatever else you need to store at the activity level)

Optionally you can also add a target (which is best explained in the activity docs)


*Feeds* are sorted containers of activities. You can easily add and remove activities from them.

*Feedly* classes (feed managers) handle the logic used in addressing the feed objects. 
They handle the complex bits of fanning out to all your followers when you create a new object (such as a tweet).


In addition there are several utility classes which you will encounter

  - Serializers (classes handling serialization of Activity objects)
  - Aggregators (utility classes for creating smart/computed feeds based on algorithms)
  - Timeline Storage (cassandra or redis specific storage functions for sorted storage)
  - Activity Storage (cassandra or redis specific storage for hash/dict based storage)
  

**Example**

```python

# the feed level

class PinFeed(CassandraFeed):
    key_format = 'feed:normal:%(user_id)s'

# basic operations on feeds

my_feed = PinFeed(13)
my_feed.add(activity)
my_feed.remove(activity)
my_feed.count()

# the manager level

class PinFeedly(Feedly):
    # this example has both a normal feed and an aggregated feed (more like
    # how facebook or wanelo uses feeds)
    feed_classes = dict(
        normal=PinFeed,
        aggregated=AggregatedPinFeed
    )
    user_feed_class = UserPinFeed

    def add_pin(self, pin):
        activity = pin.create_activity()
        # add user activity adds it to the user feed, and starts the fanout
        self.add_user_activity(pin.user_id, activity)

    def remove_pin(self, pin):
        activity = pin.create_activity()
        # removes the pin from the user's followers feeds
        self.remove_user_activity(pin.user_id, activity)

    def get_user_follower_ids(self, user_id):
        return Follow.objects.filter(target=user_id).values_list('user_id', flat=True)
```


**Features**

Feedly uses celery and Redis/Cassandra to build a system with heavy writes and extremely light reads.
It features:

  - Asynchronous tasks (All the heavy lifting happens in the background, your users don't wait for it)
  - Reusable components (You will need to make tradeoffs based on your use cases, Feedly doesnt get in your way)
  - Full Cassandra and Redis support
  - The Cassandra storage uses the new CQL3 and Python-Driver packages, which give you access to the latest Cassandra features.
  - Built for the extremely performant Cassandra 2.0
  - It supports distributed Redis calls (Threaded calls to multiple redis servers)
  

**Documentation**

[Feedly (Feed manager class) implementation] [docs_feedly]
[docs_feedly]: https://feedly.readthedocs.org/en/latest/feedly.feed_managers.html#module-feedly.feed_managers.base
[Feed class implementation] [docs_feed]
[docs_feed]: https://feedly.readthedocs.org/en/latest/feedly.feeds.html
[Choosing the right storage backend] [docs_storage_backend]
[docs_storage_backend]: https://feedly.readthedocs.org/en/latest/choosing_a_storage_backend.html
[Building notification systems] [docs_notification_systems]
[docs_notification_systems]: https://feedly.readthedocs.org/en/latest/notification_systems.html



**Background Articles**

A lot has been written about the best approaches to building feed based systems.
Here's a collection on some of the talks:

[Twitter 2013] [twitter_2013]
Redis based, database fallback, very similar to Fashiolista's old approach.

[twitter_2013]: http://highscalability.com/blog/2013/7/8/the-architecture-twitter-uses-to-deal-with-150m-active-users.html

[Etsy feed scaling] [etsy]
(Gearman, separate scoring and aggregation steps, rollups - aggregation part two)

[etsy]: http://www.slideshare.net/danmckinley/etsy-activity-feeds-architecture/

[Facebook history] [facebook]

[facebook]: http://www.infoq.com/presentations/Facebook-Software-Stack

[Django project, with good naming conventions.] [djproject]
[djproject]: http://justquick.github.com/django-activity-stream/
http://activitystrea.ms/specs/atom/1.0/
(actor, verb, object, target)

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








## Developing Feedly ##

**Vagrant**

Clone the github repo and run the following commands to setup your development environment using vagrant.
Booting a vagrant machine will take a bit of time, be sure to grab a cup of coffee while waiting for vagrant up to complete.

```bash
From the root of the feedly project run:
>>> vagrant up
>>> vagrant provision
>>> vagrant ssh
>>> cd pinterest_example
>>> python manage.py runserver 0:8000
```

Visit [192.168.50.55:8000](http://192.168.50.55:8000/) to see the example app up and running.
The most interesting bit of example code are located in:

core/pin_feed.py and core/pin_feedly.py

**Running tests**

The test suite depends on the awesome py.test library.
To run the feedly tests simply type from the root feedly folder:

```bash
>>> py.test feedly/tests
```

Cassandra tests need a Cassandra cluster up and running. 
The default address for cassandra cluster is localhost.
If you have a different address you can override this via the environment variable *TEST_CASSANDRA_HOST*

eg.
```bash
>>> TEST_CASSANDRA_HOST='192.168.1.2' py.test tests
```

The included Pinterest example app has its own test suite. You can run this by executing
```bash
>>> python pinterest_example/manage.py test core
```




