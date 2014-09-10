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

**CASSANDRA_DRIVER_KWARGS**

Extra keyword arguments sent to cassandra driver (see http://datastax.github.io/python-driver/_modules/cassandra/cluster.html#Cluster)

Defaults to ``{}``


Metric Settings
***************

**FEEDLY_METRIC_CLASS**

The metric class that will be used to collect feedly metrics.

.. note:: The default metric class is not collecting any metric and should be used as example for subclasses

Defaults to ``feedly.metrics.base.Metrics``

**FEEDLY_METRICS_OPTIONS**

A dictionary with options to send to the metric class at initialisation time.

Defaults to ``{}``
