Settings
========


Redis Settings
**************

FEEDLY_NYDUS_CONFIG

Defaults to this dict

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

FEEDLY_CASSANDRA_HOSTS

Defaults to ``['localhost']``

FEEDLY_DEFAULT_KEYSPACE

Defaults to ``feedly``

FEEDLY_CASSANDRA_CONSITENCY_LEVEL

Defaults to ``ConsistencyLevel.ONE``
