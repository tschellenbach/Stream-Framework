import datetime


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

    def append(self, activity):
        # append the activity
        self.activities.append(activity)
        
        # set the first seen
        if self.first_seen is None:
            self.first_seen = activity.time
        
        # set the last seen
        if self.last_seen is None or activity.time > self.last_seen:
            self.last_seen = activity.time
            
    @property
    def verbs(self):
        return list(set([a.verb for a in self.activities]))

    @property
    def actor_ids(self):
        return list(set([a.actor_id for a in self.activities]))

    @property
    def object_ids(self):
        return list(set([a.object_id for a in self.activities]))

    def __repr__(self):
        verbs = [v.past_tence for v in self.verbs]
        actor_ids = self.actor_ids
        object_ids = self.object_ids
        actors = ','.join(map(str, actor_ids))
        message = 'AggregatedActivity(%s-%s) Actors %s: Objects %s' % (
            self.group, ','.join(verbs), actors, object_ids)
        return message
