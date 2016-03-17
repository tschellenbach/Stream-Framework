from stream_framework import exceptions as stream_framework_exceptions
from stream_framework.utils import make_list_unique, datetime_to_epoch
from stream_framework.utils.five import long_t
import datetime
import uuid
import six


MAX_AGGREGATED_ACTIVITIES_LENGTH = 15


class BaseActivity(object):

    '''
    Common parent class for Activity and Aggregated Activity
    Check for this if you want to see if something is an activity
    '''
    pass


class DehydratedActivity(BaseActivity):

    '''
    The dehydrated verions of an :class:`Activity`.
    the only data stored is serialization_id of the original

    Serializers can store this instead of the full activity
    Feed classes

    '''

    def __init__(self, serialization_id):
        self.serialization_id = serialization_id
        self._activity_ids = [serialization_id]
        self.dehydrated = True

    def get_hydrated(self, activities):
        '''
        returns the full hydrated Activity from activities

        :param activities a dict {'activity_id': Activity}

        '''
        activity = activities[int(self.serialization_id)]
        activity.dehydrated = False
        return activity


class Activity(BaseActivity):

    '''
    Wrapper class for storing activities
    Note

    actor_id
    target_id
    and object_id are always present

    actor, target and object are lazy by default
    '''

    def __init__(self, actor, verb, object, target=None, time=None, extra_context=None):
        self.verb = verb
        self.time = time or datetime.datetime.utcnow()
        # either set .actor or .actor_id depending on the data
        self._set_object_or_id('actor', actor)
        self._set_object_or_id('object', object)
        self._set_object_or_id('target', target)
        # store the extra context which gets serialized
        self.extra_context = extra_context or {}
        self.dehydrated = False

    def get_dehydrated(self):
        '''
        returns the dehydrated version of the current activity

        '''
        return DehydratedActivity(serialization_id=self.serialization_id)

    def __eq__(self, other):
        if not isinstance(other, Activity):
            raise ValueError(
                'Can only compare to Activity not %r of type %s' % (other, type(other)))
        return self.serialization_id == other.serialization_id

    def __lt__(self, other):
       return self.serialization_id < other.serialization_id

    def __hash__(self):
        return hash(self.serialization_id)

    @property
    def serialization_id(self):
        '''
        serialization_id is used to keep items locally sorted and unique
        (eg. used redis sorted sets' score or cassandra column names)

        serialization_id is also used to select random activities from the feed
        (eg. remove activities from feeds must be fast operation)
        for this reason the serialization_id should be unique and not change over time

        eg:
        activity.serialization_id = 1373266755000000000042008
        1373266755000 activity creation time as epoch with millisecond resolution
        0000000000042 activity left padded object_id (10 digits)
        008 left padded activity verb id (3 digits)

        :returns: int --the serialization id
        '''
        if self.object_id >= 10 ** 10 or self.verb.id >= 10 ** 3:
            raise TypeError('Fatal: object_id / verb have too many digits !')
        if not self.time:
            raise TypeError('Cant serialize activities without a time')
        milliseconds = str(int(datetime_to_epoch(self.time) * 1000))
        serialization_id_str = '%s%0.10d%0.3d' % (
            milliseconds, self.object_id, self.verb.id)
        serialization_id = int(serialization_id_str)
        return serialization_id

    def _set_object_or_id(self, field, object_):
        '''
        Either write the integer to
        field_id
        Or if its a real object
        field_id = int
        field = object
        '''
        id_field = '%s_id' % field
        if isinstance(object_, six.integer_types):
            setattr(self, id_field, object_)
        elif object_ is None:
            setattr(self, field, None)
            setattr(self, id_field, None)
        else:
            setattr(self, field, object_)
            setattr(self, id_field, object_.id)

    def __getattr__(self, name):
        '''
        Fail early if using the activity class in the wrong way
        '''
        if name in ['object', 'target', 'actor']:
            if name not in self.__dict__:
                error_message = 'Field self.%s is not defined, use self.%s_id instead' % (
                    name, name)
                raise AttributeError(error_message)
        return object.__getattribute__(self, name)

    def __repr__(self):
        class_name = self.__class__.__name__
        message = '%s(%s) %s %s' % (class_name,
                                    self.verb.past_tense, self.actor_id, self.object_id)
        return message


class AggregatedActivity(BaseActivity):

    '''
    Object to store aggregated activities
    '''
    max_aggregated_activities_length = MAX_AGGREGATED_ACTIVITIES_LENGTH

    def __init__(self, group, activities=None, created_at=None, updated_at=None):
        self.group = group
        self.activities = activities or []
        self.created_at = created_at
        self.updated_at = updated_at
        # if the user opened the notification window and browsed over the
        # content
        self.seen_at = None
        # if the user engaged with the content
        self.read_at = None
        # activity
        self.minimized_activities = 0
        self.dehydrated = False
        self._activity_ids = []

    @property
    def serialization_id(self):
        '''
        serialization_id is used to keep items locally sorted and unique
        (eg. used redis sorted sets' score or cassandra column names)

        serialization_id is also used to select random activities from the feed
        (eg. remove activities from feeds must be fast operation)
        for this reason the serialization_id should be unique and not change over time

        eg:
        activity.serialization_id = 1373266755000000000042008
        1373266755000 activity creation time as epoch with millisecond resolution
        0000000000042 activity left padded object_id (10 digits)
        008 left padded activity verb id (3 digits)

        :returns: int --the serialization id
        '''
        milliseconds = str(int(datetime_to_epoch(self.updated_at)) * 1000)
        return milliseconds

    def get_dehydrated(self):
        '''
        returns the dehydrated version of the current activity

        '''
        if self.dehydrated is True:
            raise ValueError('already dehydrated')
        self._activity_ids = []
        for activity in self.activities:
            self._activity_ids.append(activity.serialization_id)
        self.activities = []
        self.dehydrated = True
        return self

    def get_hydrated(self, activities):
        '''
        expects activities to be a dict like this {'activity_id': Activity}

        '''
        assert self.dehydrated, 'not dehydrated yet'
        for activity_id in self._activity_ids:
            self.activities.append(activities[activity_id])
        self._activity_ids = []
        self.dehydrated = False
        return self

    def __len__(self):
        '''
        Works on both hydrated and not hydrated activities
        '''
        if self._activity_ids:
            length = len(self.activity_ids)
        else:
            length = len(self.activities)
        return length

    @property
    def activity_ids(self):
        '''
        Returns a list of activity ids
        '''
        if self._activity_ids:
            activity_ids = self._activity_ids
        else:
            activity_ids = [a.serialization_id for a in self.activities]
        return activity_ids

    def __eq__(self, other):
        if not isinstance(other, AggregatedActivity):
            raise ValueError(
                'I can only compare aggregated activities to other aggregated activities')
        equal = True
        date_fields = ['created_at', 'updated_at', 'seen_at', 'read_at']
        for field in date_fields:
            current = getattr(self, field)
            other_value = getattr(other, field)
            if isinstance(current, datetime.datetime) and isinstance(other_value, datetime.datetime):
                delta = abs(current - other_value)
                if delta > datetime.timedelta(seconds=10):
                    equal = False
                    break
            else:
                if current != other_value:
                    equal = False
                    break

        if self.activities != other.activities:
            equal = False

        return equal

    def __hash__(self):
        return hash(self.serialization_id)

    def contains(self, activity):
        '''
        Checks if activity is present in this aggregated
        '''
        if not isinstance(activity, (Activity, long_t, uuid.UUID)):
            raise ValueError('contains needs an activity or long not %s', activity)
        activity_id = getattr(activity, 'serialization_id', activity)
        return activity_id in set([a.serialization_id for a in self.activities])

    def append(self, activity):
        if self.contains(activity):
            raise stream_framework_exceptions.DuplicateActivityException()

        # append the activity
        self.activities.append(activity)

        # set the first seen
        if self.created_at is None:
            self.created_at = activity.time

        # set the last seen
        if self.updated_at is None or activity.time > self.updated_at:
            self.updated_at = activity.time

        # ensure that our memory usage, and pickling overhead don't go up
        # endlessly
        if len(self.activities) > self.max_aggregated_activities_length:
            self.activities.pop(0)
            self.minimized_activities += 1

    def remove(self, activity):
        if not self.contains(activity):
            raise stream_framework_exceptions.ActivityNotFound()

        if len(self.activities) == 1:
            raise ValueError(
                'removing this activity would leave an empty aggregation')

        # remove the activity
        activity_id = getattr(activity, 'serialization_id', activity)
        self.activities = [a for a in self.activities if a.serialization_id != activity_id]

        # now time to update the times
        self.updated_at = self.last_activity.time

        # adjust the count
        if self.minimized_activities:
            self.minimized_activities -= 1

    def remove_many(self, activities):
        removed_activities = []
        for activity in activities:
            try:
                self.remove(activity)
            except stream_framework_exceptions.ActivityNotFound:
                pass
            else:
                removed_activities.append(activity)
        return removed_activities

    @property
    def actor_count(self):
        '''
        Returns a count of the number of actors
        When dealing with large lists only approximate the number of actors
        '''
        base = self.minimized_activities
        actor_id_count = len(self.actor_ids)
        base += actor_id_count
        return base

    @property
    def other_actor_count(self):
        actor_count = self.actor_count
        return actor_count - 1

    @property
    def activity_count(self):
        '''
        Returns the number of activities
        '''
        base = self.minimized_activities
        base += len(self.activities)
        return base

    @property
    def last_activity(self):
        activity = self.activities[-1]
        return activity

    @property
    def last_activities(self):
        activities = self.activities[::-1]
        return activities

    @property
    def verb(self):
        return self.activities[0].verb

    @property
    def verbs(self):
        return make_list_unique([a.verb for a in self.activities])

    @property
    def actor_ids(self):
        return make_list_unique([a.actor_id for a in self.activities])

    @property
    def object_ids(self):
        return make_list_unique([a.object_id for a in self.activities])

    def is_seen(self):
        '''
        Returns if the activity should be considered as seen at this moment
        '''
        seen = self.seen_at is not None and self.seen_at >= self.updated_at
        return seen

    def update_seen_at(self):
        '''
        A hook method that updates the seen_at to current date
        '''
        self.seen_at = datetime.datetime.utcnow()

    def is_read(self):
        '''
        Returns if the activity should be considered as seen at this moment
        '''
        read = self.read_at is not None and self.read_at >= self.updated_at
        return read

    def update_read_at(self):
        '''
        A hook method that updates the read_at to current date
        '''
        self.read_at = datetime.datetime.utcnow()

    def __repr__(self):
        if self.dehydrated:
            message = 'Dehydrated AggregatedActivity (%s)' % self._activity_ids
            return message
        verbs = [v.past_tense for v in self.verbs]
        actor_ids = self.actor_ids
        object_ids = self.object_ids
        actors = ','.join(map(str, actor_ids))
        message = 'AggregatedActivity(%s-%s) Actors %s: Objects %s' % (
            self.group, ','.join(verbs), actors, object_ids)
        return message


class NotificationActivity(AggregatedActivity):

    def __init__(self, *args, **kwargs):
        AggregatedActivity.__init__(self, *args, **kwargs)

        # overrides AggregatedActivity is_read & is_seen instance methods
        self.is_seen = False
        self.is_read = False

