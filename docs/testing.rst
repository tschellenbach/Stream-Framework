Testing Feedly
===============

.. warning:: We strongly suggest against running feedly tests on a machine that is hosting redis or cassandra production data!

In order to test feedly you need to install its test requirements with 

.. code-block:: bash

	python setup.py test

or if you want more control on the test run you can use py.test entry point directly ( assuming you are in feedly root )

.. code-block:: bash

	py.test feedly/tests


The test suite connects to Redis on 127.0.0.1:6379 and to a Cassandra node on 127.0.0.1 using the native protocol.

The easiest way to run a cassandra test cluster is using the awesome `ccm package <https://github.com/pcmanus/ccm>`_

If you are not running a cassandra node on localhost you can specify a different address with the `TEST_CASSANDRA_HOST` environment variable

Every commit on Feedly is built on Travis CI, you can see the current state and the build history `here <https://travis-ci.org/tschellenbach/Feedly/builds/>`_.

If you intend to contribute to Feedly we suggest you to install pytest's coverage plugin, this way you can make sure your code changes
run during tests.
