import six


if six.PY3:
    from datetime import datetime, timedelta
    from cassandra.marshal import int64_unpack
    from cassandra.cqltypes import DateType

    # Fix for http://bugs.python.org/issue23517 issue
    def deserialize(byts, protocol_version):
        timestamp = int64_unpack(byts) / 1000.0
        dt = datetime(1970, 1, 1) + timedelta(seconds=timestamp)
        return dt
    
    DateType.deserialize = deserialize
