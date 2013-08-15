from feedly.storage.base import BaseTimelineStorage
from feedly.storage.cassandra.base_storage import CassandraBaseStorage
from pycassa.cassandra.ttypes import NotFoundException


class CassandraTimelineStorage(CassandraBaseStorage, BaseTimelineStorage):

    '''
    Uses a Column Family to store for the timeline, docs are here:
    http://pycassa.github.io/pycassa/api/pycassa/columnfamily.html
    '''

    def __init__(self, *args, **kwargs):
        CassandraBaseStorage.__init__(self, *args, **kwargs)
        BaseTimelineStorage.__init__(self, *args, **kwargs)

    def contains(self, key, activity_id):
        # TODO: are you kidding me?, index of is super slow
        try:
            return self.index_of(key, activity_id) is not None
        except ValueError:
            return False

    def index_of(self, key, activity_id):
        try:
            self.column_family.get(key, columns=(activity_id,))
        except NotFoundException:
            raise ValueError
        # TODO: this is not really efficient, but at least it seems to work :)
        # FIX THIS
        return len(list(self.column_family.get(key, column_finish=activity_id, column_count=self.count(key)))) - 1

    def get_nth_item(self, key, index):
        column_count = index + 1
        try:
            results = self.column_family.get(
                key, column_count=column_count)
            if len(results) < column_count:
                return None
            item = results.keys()[-1]
            return item
        except (IndexError, NotFoundException):
            return None

    def get_slice_from_storage(self, key, start, stop, pk_offset=False):
        '''
        :returns list: Returns a list with tuples of key,value pairs
        '''
        column_count = 10 ** 6
        column_start = '' if not pk_offset else (start or '')

        if not pk_offset and start not in (0, None):
            column_start = self.get_nth_item(key, start)
            if column_start is None:
                return []

        if stop is not None:
            column_count = (stop - (start or 0))

        try:
            results = self.column_family.get(
                key,
                column_start=column_start,
                column_count=column_count
            )
        except NotFoundException:
            return []

        return results.items()

    def add_to_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        '''
        Insert multiple columns using
        client.insert or batch_interface.insert
        '''
        client = batch_interface or self.column_family
        columns = {int(k): str(v) for k, v in activities.iteritems()}
        client.insert(key, columns)

    def remove_from_storage(self, key, activities, batch_interface=None, *args, **kwargs):
        client = batch_interface or self.column_family
        columns = map(int, activities.keys())
        client.remove(key, columns=columns)

    def count(self, key, *args, **kwargs):
        return self.column_family.get_count(key)

    def delete(self, key, *args, **kwargs):
        self.column_family.remove(key)

    def trim(self, key, length, batch_interface=None):
        '''
        Cassandra doesn't have a trim functionality
        '''
        # get the keys we want to keep as that grows less fast
        # than keys we want to remove
        results = self.get_slice_from_storage(key, None, length + 1)
        if len(results) > length:
            results = results[:length]
            # remove all data and add back what we want to keep
            self.delete(key)
            # add back the results
            activities = dict(results)
            self.add_to_storage(key, activities)
