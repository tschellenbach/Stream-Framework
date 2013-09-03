Feedly
------

[![Build Status](https://www.travis-ci.org/tschellenbach/Feedly.png?branch=cassandra)](https://www.travis-ci.org/tschellenbach/Feedly)

[![Coverage Status](https://coveralls.io/repos/tschellenbach/Feedly/badge.png?branch=cassandra)](https://coveralls.io/r/tschellenbach/Feedly?branch=cassandra)

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

Feedly uses celery and redis/cassandar to build a system which is heavy in terms of writes, but
very light for reads. 

  - Asynchronous tasks (All the heavy lifting happens in the background, your users don't wait for it)
  - Reusable components (You will need to make tradeoffs based on your use cases, Feedly doesnt get in your way)
  - Full cassandra and redis support
  - It supports distributed redis calls (Threaded calls to multiple redis servers)


**Tradeoffs**

*Store Serialized activities or ids in the feed*
Every feed contains a list of activities. But do you store the data for this activity per feed, or do you only store the id and cache the activity data.
If you store the activity plus data your feed's memory usage will increase.
If you store the id you will need to make more calls to redis upon reads.
In general you will want to store the id to reduce memory usage. Only for notification style feeds which require aggregation (John and 3 other people started following you) you might consider including
the data neccesary to determine the unique keys for aggregation.


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


**Scalable Notification Systems**

Fortunately building a scalable notification system is almost entirely identical to an activity feed. There is a feed, it is sometimes aggregated (grouped) and it contains activity.
It has a different purpose for the user:
 
 * show activity on your account vs
 * activity by your followers
 
From a tech standpoint though, the implementations are almost identical. The main objects are:

 * AggregatedActivity (Stores many activities)
 * Activity (Actor, Verb, Object, Target)
 * Verb
 
Activities are best explained with a small example:

Tommaso added your find to his list "back in black"
Activity(actor=Tommaso, verb=Add, object=find, target=list)
Vannesa loved your find
Activity(actor=Vannesa, verb=Love, object=find)
Tommaso loved your find
Activity(actor=Tommaso, verb=Love, object=find)

For notification you will often collapse the last two into:

Tommaso and Vanessa loved your find
AggregatedActivity(group=loved_find_today, first_seen, last_seen, activities, seen_at, read_at)

The storage and access logic is handled using three classes

 * NotificationFeedly (Integration between your app and the data structure)
 * NotificationFeed (Handles serialization and redis communication to store your aggregated activities)
 * Aggregator (Determines when to aggregated several activities into an aggregated activity)
 
Tutorial

Step 1 - Subclass NotificationFeed

```python
class MyNotificationFeed(NotificationFeed):
    def get_aggregator(self):
        aggregator_class = RecentVerbAggregator
        aggregator = aggregator_class()
        return aggregator
```

Step 2 - Subclass the aggregator

```python
class RecentVerbAggregator(BaseAggregator):
    '''
    Aggregates based on the same verb and same time period
    '''
    def get_group(self, activity):
        '''
        Returns a group based on the day and verb
        '''
        verb = activity.verb.id
        date = activity.time.date()
        group = '%s-%s' % (verb, date)
        return group
```

Step 3 - Test adding data

```python
feed = MyNotificationFeed(user_id)
activity = Activity(
    user_id, LoveVerb, object_id, influencer_id, time=created_at,
    extra_context=dict(entity_id=self.entity_id)
) 
feed.add(activity)
print feed[:5]
```

Step 4 - Subclass NotificationFeedly
```python
# See feedly/notification_feedly for a full example 
class MyNotificationFeedly(Feedly):
    '''
    Abstract the access to the notification feed
    '''
    def add_love(self, love):
        feed = MyNotificationFeed(user_id)
        activity = Activity(
            love.user_id, LoveVerb, love.id, love.influencer_id,
            time=love.created_at, extra_context=dict(entity_id=self.entity_id)
        ) 
        feed.add(activity)
```

**Choosing a storage layer**

Currently feedly supports both Cassandra and Redis as storage backends.

**Redis**

PROS: 

   - Easy to install
   - Super reliable
   - Easy to maintain
   - Very fast
   
CONS: 

   - Expensive memory only storage
   - Manual sharding

Redis stores data in memory. This makes sure that all operations are always fast.
It does however mean that you might need a lot of storage.

A common approach is therefor to use Redis storage for some of your feeds and fall
back to your database for less frequently requested data.

Twitter currently uses this approach and Fashiolista has used a system like this
in the first halve of 2013.

The great benefit of using Redis comes in easy of install, reliability and maintainability.
Basically it just works and there's little you need to learn to maintain it.

If you want to add a new machine to your Redis cluster you will lose part of your data.
As long as you can repopulate this data from your database this isn't a problem.

In conclusion I believe Redis is your best bet if you can fallback to the database.
You need that fallback to make sure
- Your storage costs stay under control
- You can easily bring up new redis servers

**Cassandra**

PROS:
 
   - Stores to disk
   - Automatic sharding
   - Awesome monitoring tools ([opscenter] [opscenter])

[opscenter]: http://www.datastax.com/what-we-offer/products-services/datastax-opscenter
   
CONS: 

   - Hard to install
   - Hard to maintain

Cassandra stores data to both disk and memory. Instagram has therefor recently
switched from Redis to Cassandra. Storing data to disk can potentially be a big cost saving.

In addition adding new machines to your Cassandra cluster is a breeze. Cassandra
will automatically distribute the data to new machines.

Installing Cassandra can be quite tricky. Fortunately Datastax provides [an easy AMI] [datastax_ami] to get started on AWS.

[datastax_ami]: http://www.datastax.com/documentation/cassandra/1.2/webhelp/index.html#cassandra/install/installAMILaunch.html
Cassandra is a very good option, but harder to setup and maintain than Redis.

Tips:

   - Run cassandra on c1.xlarge instances, import an many writes require a cpu heavy machine.
   - Enable both row and key caching for the column family which is used for activity storage.


 

**Hbase**

Currently HBase isn't yet supported with Feedly. However writing a storage
backend should be quite easy. If you want to have a go at it be sure to send in a pull request.



**Developing Feedly**

Clone the github repo and type vagrant up in the root directory of the project
to bring up a vagrant machine running the pinterest example.

vagrant up
vagrant ssh
python manage.py runserver

visit 192.168.50.55 the interesting bits of the example code are in
core/pin_feed.py
core/pin_feedly.py

**Running tests**

The test suite depends on the awesome py.test library you need to install to run all tests

To run the feedly tests simply type from the root feedly folder:

py.test tests

Cassandra tests need an actual cassandra cluster up and running; default address for cassandra cluster is localhost
if you have a different address you can override this via the environment variable TEST_CASSANDRA_HOST

eg.
TEST_CASSANDRA_HOST='192.168.1.2' py.test tests


For the pinterest example use the following command:
python pinterest_example/manage.py test core

 
**Testing Cassandra clustering**

You can start a cassandra test server by going to

vagrant/cassandra and typing vagrant up


**Celery setup**

Pycassa has several limitation with celery:
http://pycassa.github.io/pycassa/using_with/celery.html
TODO: Explain basic configs for celery







