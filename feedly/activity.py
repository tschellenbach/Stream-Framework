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
        #either set .actor or .actor_id depending on the data
        self._set_object_or_id('actor', actor)
        self._set_object_or_id('object', object)
        self._set_object_or_id('target', target)
        #store the extra context which gets serialized
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
        message = 'Activity(%s) %s %s' % (self.verb.past_tence, self.actor_id, self.object_id)
        return message


class AggregatedActivity(object):
    '''
    Object to store aggregated activities
    '''
    def __init__(self, unique_key, activities=None):
        self.unique_key = unique_key
        self.activities = activities or []
        
    def append(self, activity):
        self.activities.append(activity)



