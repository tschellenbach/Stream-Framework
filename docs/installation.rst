Installation
============

Installation is easy using ``pip`` both redis and cassandra dependencies are installed by the setup.

.. code-block:: bash

    $ pip install feedly --pre --process-dependency-links

or get it from source

.. code-block:: bash

    $ git clone https://github.com/tschellenbach/Feedly.git
    $ cd feedly
    $ python setup.py install


Depending on the backend you are going to use ( :ref:`choosing_a_storage_backend` ) you will need to have the backend server
up and running.


Note about pip install
----------------------

Lately every minor release of pip is doing his job in making our lives more complicated and painful.

If you are running older verions of pip (1.4 or older) you need a different install command

users of pip < 1.4 must use this command

.. code-block:: bash

    $ pip install feedly


and users of pip ~= 1.4 this one

.. code-block:: bash

    $ pip install feedly --pre

you can see your pip version via this command

.. code-block:: bash

    $ pip --version
