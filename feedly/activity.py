import datetime
from collections import deque
from feedly import exceptions as feedly_exceptions
import copy
from feedly.utils import make_list_unique

MAX_AGGREGATED_ACTIVITIES_LENGTH = 99


class Activity(object):
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
        self.time = time or datetime.datetime.today()
        # either set .actor or .actor_id depending on the data
        self._set_object_or_id('actor', actor)
        self._set_object_or_id('object', object)
        self._set_object_or_id('target', target)
        # store the extra context which gets serialized
        self.extra_context = extra_context or {}

    def __cmp__(self, other):
        equal = True
        if isinstance(self.time, datetime.datetime) and isinstance(other.time, datetime.datetime):
            delta = self.time - other.time
            if abs(delta) > datetime.timedelta(seconds=10):
                equal = False
        else:
            if self.time != other.time:
                equal = False

        important_fields = ['actor_id', 'object_id', 'target_id',
                            'extra_context', 'verb']
        for field in important_fields:
            value = getattr(self, field)
            comparison_value = getattr(other, field)
            if value != comparison_value:
                equal = False
                break
        return_value = 0 if equal else -1

        return return_value

    @property
    def serialization_id(self):
        id_ = '%s,%s' % (self.verb.id, self.object_id)
        return id_

    def _set_object_or_id(self, field, object_):
        '''
        Either write the integer to
        field_id
        Or if its a real object
        field_id = int
        field = object
        '''
        id_field = '%s_id' % field
        if isinstance(object_, (int, long)):
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
                error_message = 'Field self.%s is not defined, use self.%s_id instead' % (name, name)
                raise AttributeError(error_message)
        return object.__getattribute__(self, name)

    def __repr__(self):
        message = 'Activity(%s) %s %s' % (
            self.verb.past_tence, self.actor_id, self.object_id)
        return message


class AggregatedActivity(object):
    '''
    Object to store aggregated activities
    '''
    def __init__(self, group, activities=None, first_seen=None, last_seen=None):
        self.group = group
        self.activities = activities or []
        self.first_seen = first_seen
        self.last_seen = last_seen
        # if the user opened the notification window and browsed over the content
        self.seen_at = None
        # if the user engaged with the content
        self.read_at = None
        # activity
        self.minimized_activities = 0

    def __cmp__(self, other):
        equal = True

        date_fields = ['first_seen', 'last_seen', 'seen_at', 'read_at']
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

        return_value = 0 if equal else -1

        return return_value

    def contains(self, activity):
        '''
        Checks if the time normalized version of the activity
        is already present in this aggregated activity
        '''
        # make sure we don't modify things in place
        activities = copy.deepcopy(self.activities)
        activity = copy.deepcopy(activity)

        # we don't care about the time of the activity, just the contents
        activity.time = None
        for a in activities:
            a.time = None

        present = activity in activities

        return present

    def append(self, activity):
        if self.contains(activity):
            raise feedly_exceptions.DuplicateActivityException()

        # append the activity
        self.activities.append(activity)

        # set the first seen
        if self.first_seen is None:
            self.first_seen = activity.time

        # set the last seen
        if self.last_seen is None or activity.time > self.last_seen:
            self.last_seen = activity.time

        # ensure that our memory usage, and pickling overhead don't go up endlessly
        if len(self.activities) > MAX_AGGREGATED_ACTIVITIES_LENGTH:
            self.activities.pop(0)
            self.minimized_activities += 1

    @property
    def actor_count(self):
        '''
        Returns a count of the number of actors
        When dealing with large lists only approximate the number of actors
        '''
        base = self.minimized_activities
        actor_ids = self.actor_ids
        base += len(actor_ids)
        return base

    @property
    def other_actor_count(self):
        actor_count = self.actor_count
        return actor_count - 2

    @property
    def activity_count(self):
        '''
        Returns the number of activities
        '''
        base = self.minimized_activities
        base += len(self.activities)
        return base

    @property
    def last_activities(self):
        activities = self.activities[::-1]
        return activities

    @property
    def last_activity(self):
        activity = self.activities[-1]
        return activity

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
        seen = self.seen_at is not None and self.seen_at > self.last_seen
        return seen

    def __repr__(self):
        verbs = [v.past_tence for v in self.verbs]
        actor_ids = self.actor_ids
        object_ids = self.object_ids
        actors = ','.join(map(str, actor_ids))
        message = 'AggregatedActivity(%s-%s) Actors %s: Objects %s' % (
            self.group, ','.join(verbs), actors, object_ids)
        return message
