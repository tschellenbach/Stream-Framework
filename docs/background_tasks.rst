Background Tasks with celery
============================

Stream Framework uses celery to do the heavy fanout write operations in the background.

We really suggest you to have a look at `celery documentation`_  if you are not familiar with the project.

**Fanout**

When an activity is added Stream Framework will perform a fanout to all subscribed feeds.
The base Stream Framework manager spawns one celery fanout task every 100 feeds.
Change the value of `fanout_chunk_size` of your manager if you think this number is too low/high for you.

Few things to keep in mind when doing so:

1. really high values leads to a mix of heavy tasks and light tasks (not good!)
2. publishing and consuming tasks introduce some overhead, dont spawn too many tasks
3. Stream Framework writes data in batches, thats a really good optimization you want to keep
4. huge tasks have more chances to timeout

.. note:: When developing you can run fanouts without celery by setting `CELERY_ALWAYS_EAGER = True`


Prioritise fanouts
********************************

Stream Framework partition fanout tasks in two priority groups.
Fanouts with different priorities do exactly the same operations (adding/removing activities from/to a feed)
the substantial difference is that they get published to different queues for processing.
Going back to our pinterest example app, you can use priorities to associate more resources to fanouts that target
active users and send the ones for inactive users to a different cluster of workers.
This also make it easier and cheaper to keep active users' feeds updated during activity spikes because you dont need
to scale up capacity less often.

Stream Framework manager is the best place to implement your high/low priority fanouts, in fact the `get_follower_ids` method
is required to return the feed ids grouped by priority.

eg::

	class MyStreamManager(Manager):
	
	    def get_user_follower_ids(self, user_id):
	    	follower_ids = {
	        	FanoutPriority.HIGH: get_follower_ids(user_id, active=True),
	        	FanoutPriority.LOW: get_follower_ids(user_id, active=False)
	        }
	        return follower_ids


Celery and Django
*****************

If this is the time you use Celery and Django together I suggest you should `follow this document's instructions <https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html>`_.	

It will guide you through the required steps to get Celery background processing up and running.


Using other job queue libraries
********************************

As of today background processing is tied to celery.

While we are not planning to support different queue jobs libraries in the near future using something different than celery
should be quite easy and can be mostly done subclassing the feeds manager.

.. _celery documentation: http://docs.celeryproject.org/en/latest/
