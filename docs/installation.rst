Installation
============

Installation is easy using ``pip`` both redis and cassandra dependencies are installed by the setup.

First of all check the version of pip installed on your system

.. code-block:: bash

    $ pip --version

If your version is 1.5 or higher use this install command

.. code-block:: bash

    $ pip install feedly --process-dependency-links

users of later versions of pip should use this command

.. code-block:: bash

    $ pip install feedly


or get it from source

.. code-block:: bash

    $ git clone https://github.com/tschellenbach/Feedly.git
    $ cd feedly
    $ python setup.py install


Depending on the backend you are going to use ( :ref:`choosing_a_storage_backend` ) you will need to have the backend server
up and running.

