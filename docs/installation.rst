Installation
============

Installation is easy using ``pip``, choose redis or cassandra dependencies.


.. code-block:: bash

    $ pip install Stream-Framework[redis]

or

.. code-block:: bash

    $ pip install Stream-Framework[cassandra2]

or

.. code-block:: bash

    $ pip install Stream-Framework[cassandra3]


or get it from source

.. code-block:: bash

    $ git clone https://github.com/tschellenbach/Stream-Framework.git
    $ cd Stream-Framework
    $ python setup.py install


Depending on the backend you are going to use ( :ref:`choosing_a_storage_backend` ) you will need to have the backend server
up and running.

