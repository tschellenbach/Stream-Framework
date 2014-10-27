.. _cassandra_backend:

Cassandra storage backend
=========================

This document is specific to the Cassandra backend.

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
