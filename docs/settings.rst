Settings
========

.. note:: Settings currently only support Django settings. To add support for Flask or other frameworks simply change feedly.settings.py

Redis Settings
**************

**FEEDLY_REDIS_CONFIG**

The settings for redis, keep here the list of redis servers you want to use for feedly storage

Defaults to

.. code-block:: python

    FEEDLY_REDIS_CONFIG = {
        'default': {
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            'password': None
        },
    }

Cassandra Settings
******************

**FEEDLY_CASSANDRA_HOSTS**

The list of nodes that are part of the cassandra cluster.

.. note:: You dont need to put every node of the cluster, cassandra-driver has built-in node discovery

Defaults to ``['localhost']``

**FEEDLY_DEFAULT_KEYSPACE**

The cassandra keyspace where feed data is stored

Defaults to ``feedly``

**FEEDLY_CASSANDRA_CONSISTENCY_LEVEL**

The consistency level used for both reads and writes to the cassandra cluster.

Defaults to ``cassandra.ConsistencyLevel.ONE``

**FEEDLY_TRACK_METRICS**

Enable cassandra driver metrics, if enabled the connection will track metrics using python scales
You need to configure python scales (which comes installed as a dependency) in order to actually use those metrics

Defaults to ``False``




