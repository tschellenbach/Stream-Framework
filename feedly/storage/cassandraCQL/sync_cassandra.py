from cqlengine.management import create_table
from feedly.storage.cassandraCQL.models import Activity
from feedly.storage.cassandraCQL import connection# import setup_connection

connection.setup_connection()
create_table(Activity, create_missing_keyspace=True)
