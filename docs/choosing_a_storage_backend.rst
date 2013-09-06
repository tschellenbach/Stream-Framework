
**Choosing a storage layer**

Currently Feedly supports both `Cassandra <http://www.datastax.com/>`_ and `Redis <http://www.redis.io/>`_ as storage backends.

**Summary**

Redis is super easy to get started with and works fine for smaller use cases.
If you're just getting started use Redis. 
When your data requirements become larger though it becomes really expensive
to store all the data in Redis and Cassandra becomes the better choice.


**Redis**

PROS:

-  Easy to install
-  Super reliable
-  Easy to maintain
-  Very fast

CONS:

-  Expensive memory only storage
-  Manual sharding

Redis stores data in memory. This makes sure that all operations are
always fast. It does however mean that you might need a lot of storage.

A common approach is therefor to use Redis storage for some of your
feeds and fall back to your database for less frequently requested data.

Twitter currently uses this approach and Fashiolista has used a system
like this in the first halve of 2013.

The great benefit of using Redis comes in easy of install, reliability
and maintainability. Basically it just works and there's little you need
to learn to maintain it.

If you want to add a new machine to your Redis cluster you will lose
part of your data. As long as you can repopulate this data from your
database this isn't a problem.

In conclusion I believe Redis is your best bet if you can fallback to
the database. You need that fallback to make sure - Your storage costs
stay under control - You can easily bring up new redis servers

**Cassandra**

PROS:

-  Stores to disk
-  Automatic sharding
-  Awesome monitoring tools
   (`opscenter <http://www.datastax.com/what-we-offer/products-services/datastax-opscenter>`_)

CONS:

-  Hard to install
-  Hard to maintain

Cassandra stores data to both disk and memory. Instagram has therefor
recently switched from Redis to Cassandra. Storing data to disk can
potentially be a big cost saving.

In addition adding new machines to your Cassandra cluster is a breeze.
Cassandra will automatically distribute the data to new machines.

Installing Cassandra can be quite tricky. Fortunately Datastax provides
`an easy
AMI <http://www.datastax.com/documentation/cassandra/1.2/webhelp/index.html#cassandra/install/installAMILaunch.html%20Cassandra%20is%20a%20very%20good%20option,%20but%20harder%20to%20setup%20and%20maintain%20than%20Redis.>`_
to get started on AWS.

Tips:

-  Run cassandra on c1.xlarge instances, import an many writes require a
   cpu heavy machine.
-  Enable both row and key caching for the column family which is used
   for activity storage.

**Hbase**

Currently HBase isn't yet supported with Feedly. However writing a
storage backend should be quite easy. If you want to have a go at it be
sure to send in a pull request.
