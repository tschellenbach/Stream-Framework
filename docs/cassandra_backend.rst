.. _cassandra_backend:

Cassandra storage backend
=========================

This document is specific to the Cassandra backend.

Create keyspace and columnfamilies
**********************************

Keyspace and columnfamilies for your feeds can be created via cqlengine's sync_table.

::

    from myapp.feeds import MyCassandraFeed
    from cqlengine.management import sync_table

    timeline = MyCassandraFeed.get_timeline_storage()
    sync_table(timeline.model)


sync_table can also create missing columns but it will never delete removed columns.


Use a custom activity model
***************************

Since the Cassandra backend is using CQL3 column families, activities have a predefined schema. Cqlengine is used
to read/write data from and to Cassandra. 

::


    from stream_framework.storage.cassandra import models


    class MyCustomActivity(models.Activity)
        actor = columns.Bytes(required=False)


    class MySuperAwesomeFeed(CassandraFeed):
        timeline_model = MyCustomActivity


Remember to resync your column family when you add new columns (see above).
