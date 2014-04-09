The activity model
==================


Extend the activity model
*************************

.. versionadded:: 0.10.0

You can subclass the activity model to add your own methods.
After you've created your own activity model you need to hook it
up to the feed. An example follows below

::

	from feedly.activity import Activity
	
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

	from feedly.activity import AggregatedActivity
	
	# define the custom aggregated activity
	class CustomAggregated(AggregatedActivity):
	    pass
	    
	# hook the custom classes up to the feed
	class RedisCustomAggregatedFeed(RedisAggregatedFeed):
	    activity_class = CustomActivity
	    aggregated_activity_class = CustomAggregated



Adding new verbs
****************

Registering a new verb is quite easy.
Just subclass the Verb class and give it a unique id.

::


    from feedly.verbs import register
    from feedly.verbs.base import Verb
    
    
    class Pin(Verb):
        id = 5
        infinitive = 'pin'
        past_tense = 'pinned'
    
    register(Pin)
        
.. seealso:: Make sure your verbs are registered before you read data from feedly, if you use django
you can just define/import them in models.py to make sure they are loaded early


Activity serialization
**********************


Activity order and uniqueness
*****************************


Aggregated activities
*********************

