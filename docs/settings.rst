Settings
========

.. note:: Settings currently only support Django settings. To add support for Flask or other frameworks simply change feedly.settings.py

Redis Settings
**************

**FEEDLY_NYDUS_CONFIG**

The nydus settings for redis, keep here the list of redis servers you want to use for feedly storage

Defaults to

.. code-block:: python

    {
        'CONNECTIONS': {
            'redis': {
                'engine': 'nydus.db.backends.redis.Redis',
                'router': 'nydus.db.routers.redis.PrefixPartitionRouter',
                'hosts': {
                    0: {'prefix': 'default', 'db': 0, 'host': 'localhost', 'port': 6379},
                }
            },
        }
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




