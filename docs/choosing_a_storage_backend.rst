.. _choosing_a_storage_backend:

Choosing a storage layer
========================

Currently Stream Framework supports both `Cassandra <http://www.datastax.com/>`_ and `Redis <http://www.redis.io/>`_ as storage backends.

**Summary**

Redis is super easy to get started with and works fine for smaller use cases.
If you're just getting started use Redis. 
When your data requirements become larger though it becomes really expensive
to store all the data in Redis. For larger use cases we therefor recommend Cassandra.


Redis (2.7 or newer)
********************

PROS:

-  Easy to install
-  Super reliable
-  Easy to maintain
-  Very fast

CONS:

-  Expensive memory only storage
-  Manual sharding

Redis stores its complete dataset in memory. This makes sure that all operations are
always fast. It does however mean that you might need a lot of storage.

A common approach is therefor to use Redis storage for some of your
feeds and fall back to your database for less frequently requested data.

Twitter currently uses this approach and Fashiolista has used a system
like this in the first half of 2013.

The great benefit of using Redis comes in easy of install, reliability
and maintainability. Basically it just works and there's little you need
to learn to maintain it.

Redis doesn't support any form of cross machine distribution. So if you add a new
node to your cluster you need to manual move or recreate the data.

In conclusion I believe Redis is your best bet if you can fallback to
the database when needed.

Cassandra (2.0 or newer)
************************

PROS:

-  Stores to disk
-  Automatic sharding across nodes
-  Awesome monitoring tools
   (`opscenter <http://www.datastax.com/what-we-offer/products-services/datastax-opscenter>`_)

CONS:

-  Not as easy to setup
-  Hard to maintain

Cassandra stores data to both disk and memory. Instagram has recently switched from Redis to Cassandra. 
Storing data to disk can potentially be a big cost saving.

In addition adding new machines to your Cassandra cluster is a breeze.
Cassandra will automatically distribute the data to new machines.

If you are using amazon EC2 we suggest you to try Datastax's easy
`AMI <http://www.datastax.com/documentation/cassandra/1.2/webhelp/index.html#cassandra/install/installAMILaunch.html%20Cassandra%20is%20a%20very%20good%20option,%20but%20harder%20to%20setup%20and%20maintain%20than%20Redis.>`_
to get started on AWS.


