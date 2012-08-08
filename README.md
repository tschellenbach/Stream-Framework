Feedly
------

Feedly allows you to build complex feed and caching structures using Redis.

**What is a feed?**

A feed is a stream of content which is created by people or subjects you follow.
Prime examples are the Facebook newsfeed, your Twitter stream or your Pinterest following page.

Feeds are commonly also called: Activity Streams, activity feeds, news streams.

**Why is it hard?**

It's very hard to split up data for social sites. You can't easily store all Facebook users in Brasil on one server and the ones in The Netherlands on another. One of the recommended approaches to this problem is to publish your activity (ie a tweet on twitter) to all of your followers. These streams of content are hard to maintain and keep up to date, but they are really fast for the user and can easily be sharded.

**Feedly**

Feedly allows you to easily use Redis and Celery (an awesome task broker) to build infinitely scalable feeds.
The core functionality is located in 3 core classes.

  - Structures
  - Activities
  - Feeds
  - Feed managers (Feedly)

Structures are basic building blocks wrapping python functionality around Redis datastructures. There are convenient objects for hashes, lists and sorted sets.

Activities is the content which is stored in a feed. It follows the nomenclatura from the [activity stream spec] [astream]
[astream]: http://activitystrea.ms/specs/atom/1.0/#activity.summary
Every activity therefor stores at least:

  - Time (the time of the activity)
  - Verb (the action, ie loved, liked, followed)
  - Actor (the user id doing the action)
  - Object (the object the action is related to)
  - Extra context (Used for whatever else you need to store at the activity level)

Optionally you can also add a target (which is best explained in the activity docs)


Feeds are sorted containers of activities. They extend upon the data structures and add custom serialization logic and behavior.

Feedly classes (feed managers)
Handle the logic used in addressing the feed objects. They handle the complex bits of fanning out to all your followers when you create a new object (such as a tweet).


In addition there are several utility classes which you will encounter

  - Serializers (classes handling serialization of Activity objects)
  - Aggregators (utility classes for creating smart/computed feeds based on algorithms)
  - Marker (FeedEndMarker, marker class allowing you to correctly cache an empty feed)

**Example**

```python
#Feedly level, on the background this spawns hundreds of tasks to update the feeds of your followers
feedly = LoveFeedly.add_love(love)

#Feed level, show the activities stored in the feed
feed = LoveFeed(user_id)
images = feed[:20]
```

**Features**

Feedly uses celery and redis to build a system which is heavy in terms of writes, but
very light for reads. 

  - Asynchronous tasks (all the heavy lifting happens in the background, your users don't wait for it)
  - It supports distributed redis calls (Threaded calls to multiple redis servers)


**Background Articles**

A lot has been written about the best approaches to building feed based systems.
Here's a collection on some of the talks:

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


