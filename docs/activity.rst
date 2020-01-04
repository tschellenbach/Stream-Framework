Activity class
==================

Activity is the core data in Stream Framework; their implementation follows the `activitystream schema specification <http://activitystrea.ms/specs/atom/1.0/>`_.
An activity in Stream Framework is composed by an actor, a verb and an object; for example: "Geraldine posted a photo".
The data stored in activities can be extended if necessary; depending on how you use Stream Framework you might want to store some extra information or not.
Here is a few good rule of thumbs to follow in case you are not sure whether some information should be stored in Stream Framework:

Good choice:

1. Add a field used to perform aggregation (eg. object category)
2. You want to keep every piece of information needed to work with activities in Stream Framework (eg. avoid database lookups)

Bad choice:

1. The data stored in the activity gets updated
2. The data requires lot of storage


Activity storage strategies
***************************

Activities are stored on Stream Framework trying to maximise the benefits of the storage backend used.

When using the redis backend Stream Framework will keep data denormalized; activities are stored in a special storage (activity storage) and user feeds only 
keeps a reference (activity_id / serialization_id).
This allow Stream Framework to keep the (expensive) memory usage as low as possible.

When using Cassandra as storage Stream Framework will denormalize activities; there is not an activity storage but instead every user feed will keep the complete
activity.
Doing so allow Stream Framework to minimise the amount of Cassandra nodes to query when retrieving data or writing to feeds.

In both storages activities are always stored in feeds sorted by their creation time (aka Activity.serialization_id).


Extend the activity class
*************************

.. versionadded:: 0.10.0

You can subclass the activity model to add your own methods.
After you've created your own activity model you need to hook it
up to the feed. An example follows below

::

	from stream_framework.activity import Activity
	
	# subclass the activity object
	class CustomActivity(Activity):
		def mymethod():
			pass
			
	# hookup the custom activity object to the Redis feed
	class CustomFeed(RedisFeed):
		activity_class = CustomActivity

    	
For aggregated feeds you can customize both the activity and the aggregated activity object.
You can give this a try like this

::

	from stream_framework.activity import AggregatedActivity
	
	# define the custom aggregated activity
	class CustomAggregated(AggregatedActivity):
	    pass
	    
	# hook the custom classes up to the feed
	class RedisCustomAggregatedFeed(RedisAggregatedFeed):
	    activity_class = CustomActivity
	    aggregated_activity_class = CustomAggregated





Activity serialization
**********************


Activity order and uniqueness
*****************************


Aggregated activities
*********************

