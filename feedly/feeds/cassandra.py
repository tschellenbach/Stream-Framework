from feedly.serializers.activity_serializer import ActivitySerializer
from pycassa import NotFoundException


class BaseFeed(object):
    column_family = None
    serializer_class = ActivitySerializer
    max_length = 5

    def count(self):
        return self.column_family.store.get_count(self.key)

    def get_nth_item(self, index):
        '''
        this is expensive it costs O(N) to get to know the column
        given its index

        TODO: change the way we access feeds (paginate using items will fix this)
        '''
        try:
            return self.column_family.store.get(self.key, column_count=index + 1).keys()[-1]
        except NotFoundException:
            return None

    def get_results(self, start=None, stop=None):
        '''
        TODO: this just does not work efficently with cassandra
        because it does not support OFFSET kind of query
        (no matter where you try to do you need an index for that)
        '''

        column_count = None
        column_start = ''

        if start not in (0, None):
            column_start = self.get_nth_item(start)

        if stop is not None:
            column_count = (stop - start or 0) + 1

        try:
            results = self.column_family.store.get(
                self.key,
                column_start=column_start,
                column_count=column_count
            )
        except NotFoundException:
            return []
        else:
            return self.deserialize_activities(results)

    def add(self, activity):
        '''
        Make sure results are actually cleared to max items
        '''
        activities = [activity]
        result = self.add_many(activities)[0]
        return result

    def remove(self, activity):
        '''
        Delegated to remove many
        '''
        activities = [activity]
        result = self.remove_many(activities)[0]
        return result

    @property
    def model(self):
        return self.column_family.model

    def contains(self, activity):
        try:
            self.column_family.store.get(
                self.key, columns=(activity.serialization_id,)
            )
        except NotFoundException:
            return False
        else:
            return True

    def delete(self):
        self.column_family.store.remove(self.key)

    def serialize_activity(self, activity):
        '''
        Serialize the activity into something we can store in Redis
        '''
        serialized_activity = self.serializer.dumps(activity)
        return serialized_activity

    def deserialize_activities(self, serialized_activities):
        '''
        Reverse the serialization
        '''
        activities = []
        for serialized, score in serialized_activities:
            activity = self.serializer.loads(serialized)
            activities.append(activity)
        return activities

    def get_serializer(self):
        '''
        Returns an instance of the serialization class
        '''
        return self.serializer_class()

    def trim(self, max_length=None):
        pass
