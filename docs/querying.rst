Querying feeds
==============

You can query the feed using Python slicing. In addition you can order
and filter the feed on several predefined fields. Examples are shown below


**Slicing**::

	feed = RedisFeed(13)
	activities = feed[:10]


**Filtering and Pagination**::

    feed.filter(activity_id__gte=1)[:10]
    feed.filter(activity_id__lte=1)[:10]
    feed.filter(activity_id__gt=1)[:10]
    feed.filter(activity_id__lt=1)[:10]
    

    
**Ordering feeds**

.. versionadded:: 0.10.0
This is only supported using Cassandra and Redis at the moment.

::

	feed.order_by('activity_id')
	feed.order_by('-activity_id')
