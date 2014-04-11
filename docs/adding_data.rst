Adding data
===========

You can add an Activity object to the feed using the add or add_many instructions.


.. code:: python


    feed = UserPinFeed(13)
    feed.add(activity)
    
    # add many example
    feed.add_many([activity])
    

    
**What's an activity**

The activity object is best described using an example.
For Pinterest for instance a common activity would look like this:

Thierry added an item to his board Surf Girls.

In terms of the activity object this would translate to::

	Activity(
		actor=13, # Thierry's user id
		verb=1, # The id associated with the Pin verb
		object=1, # The id of the newly created Pin object
		target=1, # The id of the Surf Girls board
		time=datetime.utcnow(), # The time the activity occured
	)
	
The names for these fields are based on the `activity stream spec 
<http://activitystrea.ms/specs/atom/1.0/>`_.



