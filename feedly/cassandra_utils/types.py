from feedly.utils import epoch_to_datetime, datetime_to_epoch
import pycassa

class DatetimeType(pycassa.types.CassandraType):

    @staticmethod
    def pack(intval):
        return str(datetime_to_epoch(intval))

    @staticmethod
    def unpack(strval):
        return epoch_to_datetime(strval)