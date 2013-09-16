Background Tasks with celery
============================

Feedly uses celery to do the heavy fanout write operations in the background.

We really suggest you to have a look at `celery documentation`_  if you are not familiar with the project.

**Fanout**

When an activity is added feedly will perform a fanout to all subscribed feeds.
The base feedly manager spawns one celery fanout task every 100 feeds.
Change the value of `fanout_chunk_size` of your manager if you think this number is too low/high for you.

Few things to keep in mind when doing so:

1. really high values leads to a mix of heavy tasks and light tasks (not good!)
2. publishing and consuming tasks introduce some overhead, dont spawn too many tasks
3. feedly writes data in batches, thats a really good optimization you want to keep
4. huge tasks have more chances to timeout

.. note:: When developing you can run fanouts without celery by setting `CELERY_ALWAYS_EAGER = True`


Using other job queue libraries
********************************

As of today feedly background processing is tied to celery.

While we are not planning to support different queue jobs libraries in the near future using something different than celery
should be quite easy and can be mostly done subclassing the feedly manager.

.. _celery documentation: http://docs.celeryproject.org/en/latest/