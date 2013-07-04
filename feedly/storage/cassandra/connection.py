from pycassa.pool import ConnectionPool


def get_cassandra_connection(keyspace_name, hosts):
    if get_cassandra_connection._connection is None:
        get_cassandra_connection._connection = ConnectionPool(keyspace_name, hosts)
    return get_cassandra_connection._connection

get_cassandra_connection._connection = None