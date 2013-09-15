Testing Feedly
===============

.. warning:: We strongly suggest against running feedly tests on a machine that is hosting redis or cassandra production data!

In order to test feedly you need to install its test requirements via `python setup.py test`

Every commit on Feedly is built on Travis CI, you can see the current state and the build history here.

Most of feedly tests require a redis server and a cassandra node, by default Feedly will try to connect to localhost.

If you are not running a cassandra node on localhost you can specify a different address with the `TEST_CASSANDRA_HOST` environment variable


.. code-block:: bash

	TEST_CASSANDRA_HOST='192.168.50.55' py.test tests/storage/cassandra.py -s -l


If you intend to contribute to Feedly we suggest you to install pytest's coverage plugin, this way you can make sure your code contributions
are at least executed during tests.
