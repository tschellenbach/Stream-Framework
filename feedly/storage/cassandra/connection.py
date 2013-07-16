from pycassa.pool import ConnectionPool


def get_cassandra_connection(keyspace_name, hosts):
    if get_cassandra_connection._connection is None:
        get_cassandra_connection._connection = ConnectionPool(
            keyspace_name, hosts, pool_size=len(hosts)*24,
            prefill=False, timeout=10)
    return get_cassandra_connection._connection

get_cassandra_connection._connection = None
