Stream Framework Design
-----------------------

*The first approach*

A first feed solution usually looks something like this:

.. code:: sql

    SELECT * FROM tweets
    JOIN follow ON (follow.target_id = tweet.user_id)
    WHERE follow.user_id = 13

This works in the beginning, and with a well tuned database will keep on
working nicely for quite some time. However at some point the load
becomes too much and this approach falls apart. Unfortunately it's very
hard to split up the tweets in a meaningfull way. You could split it up
by date or user, but every query will still hit many of your shards.
Eventually this system collapses, read more about this in `Facebook's
presentation <http://www.infoq.com/presentations/Facebook-Software-Stack>`__.

*Push or Push/Pull*

In general there are two similar solutions to this
problem.

In the push approach you publish your activity (ie a tweet on twitter)
to all of your followers. So basically you create a small list per user
to which you insert the activities created by the people they follow.
This involves a huge number of writes, but reads are really fast they
can easily be sharded.

For the push/pull approach you implement the push based systems for a
subset of your users. At Fashiolista for instance we used to have a push
based approach for active users. For inactive users we only kept a small
feed and eventually used a fallback to the database when we ran out of
results.

**Stream Framework**

Stream Framework allows you to easily use Cassndra/Redis and Celery (an awesome
task broker) to build infinitely scalable feeds. The high level
functionality is located in 4 classes.

-  Activities
-  Feeds
-  Feed managers
-  Aggregators

*Activities* are the blocks of content which are stored in a feed. It
follows the nomenclatura from the [activity stream spec] [astream]
[astream]: http://activitystrea.ms/specs/atom/1.0/#activity.summary
Every activity therefor stores at least:

-  Time (the time of the activity)
-  Verb (the action, ie loved, liked, followed)
-  Actor (the user id doing the action)
-  Object (the object the action is related to)
-  Extra context (Used for whatever else you need to store at the
   activity level)

Optionally you can also add a target (which is best explained in the
activity docs)

*Feeds* are sorted containers of activities. You can easily add and
remove activities from them.

*Stream Framework* classes (feed managers) handle the logic used in addressing the
feed objects. They handle the complex bits of fanning out to all your
followers when you create a new object (such as a tweet).

In addition there are several utility classes which you will encounter

-  Serializers (classes handling serialization of Activity objects)
-  Aggregators (utility classes for creating smart/computed feeds based
   on algorithms)
-  Timeline Storage (cassandra or redis specific storage functions for
   sorted storage)
-  Activity Storage (cassandra or redis specific storage for hash/dict
   based storage)
