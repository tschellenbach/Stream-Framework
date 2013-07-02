from feedly.feeds.base import BaseFeed
from feedly.marker import FeedEndMarker, FEED_END
from feedly.serializers.love_activity_serializer import LoveActivitySerializer
from feedly.structures.sorted_set import RedisSortedSetCache
from feedly.utils import time_asc, get_user_model
from feedly.storage.cassandra import FEED_STORE
from feedly.storage.cassandra import LOVE_ACTIVITY
import logging


logger = logging.getLogger(__name__)


ACTIVE_USER_MAX_LENGTH = 25 * 150 + 1
INACTIVE_USER_MAX_LENGTH = 25 * 3 + 1
BATCH_FOLLOW_MAX_LOVES = 25 * 3 + 1


class LoveFeed(BaseFeed):

    '''
    The love Feed class

    It implements the feed logic

    TODO: rename it Feed :)

    '''
    column_family = FEED_STORE
    default_max_length = ACTIVE_USER_MAX_LENGTH
    key_format = 'love_feed_%s'
    serializer_class = LoveActivitySerializer

    def __init__(self, user_id, max_length=None):
        # Whats max_length for ??
        from feedly.feed_managers.love_feedly import LoveFeedly
        self.manager = LoveFeedly
        # input validation
        if not isinstance(user_id, int):
            raise ValueError('user id should be an int, found %r' % user_id)
        # support for different serialization schemes
        self.serializer = self.serializer_class()
        self.user_id = user_id
        self.key = self.key_format % user_id
        self._max_length = max_length

    def add(self, activity, *arg, **kwargs):
        '''
        Make sure results are actually cleared to max items
        '''
        activities = [activity]
        result = self.add_many(activities, *arg, **kwargs)
        return result

    def add_many(self, activities):
        '''
        We use pipelining for doing multiple adds
        Alternatively we could also send multiple adds to one call.
        Don't see a reason for that though
        '''
        batch_insert = {
            self.key: {}
        }
        columns = batch_insert[self.key]
        for activity in activities:
            # TODO: we should use timestamp as column name
            activity_id = activity.serialization_id
            columns[activity_id] = str(activity_id)
        insert_results = self.column_family.store.batch_insert(batch_insert)
        # make sure we trim to max length
        self.trim()
        return insert_results

    def remove(self, activity):
        '''
        Delegated to remove many
        '''
        activities = [activity]
        result = self.remove_many(activities)[0]
        return result

    def remove_many(self, activities):
        '''
        Efficiently remove many activities
        '''
        columns = []
        for activity in activities:
            columns.append(activity.serialization_id)
        results = self.column_family.remove(
            self.model(key=self.key), columns=columns
        )
        return results

    @property
    def max_length(self):
        '''
        Allow us to overwrite the max length at a per user level
        '''
        max_length = getattr(
            self, '_max_length', self.default_max_length) or self.default_max_length
        return max_length

    def deserialize_activities(self, activities):
        '''
        Reverse the serialization
        '''
        activity_ids = [activity_id for activity_id in activities]
        activity_dict = LOVE_ACTIVITY.multiget(activity_ids)

        activity_objects = []
        for activity_id in activities:
            serialized_activity = activity_dict.get(activity_id)
            # sometimes there is no serialized activity, this happens when
            # the data is removed from redis and the database fallback
            # in this case we simply return less results
            if not serialized_activity:
                logger.warn(
                    'Cant find love with id %s, excluding it from the feed', activity_id)
                continue
            activity = self.serializer.loads(serialized_activity)
            activity_objects.append(activity)
        return activity_objects


def convert_activities_to_loves(activities):
    '''
    Turns our activities into loves
    '''
    from entity.models import Love
    from entity.cache_objects import entity_cache
    user_ids = [a.actor_id for a in activities]
    entity_ids = [a.extra_context['entity_id'] for a in activities]
    user_dict = get_user_model().objects.get_cached_users(user_ids)
    entity_dict = entity_cache[entity_ids]

    loves = []

    def complete(activity):
        missing = dict()
        actor = user_dict.get(activity.actor_id, missing)
        entity_id = activity.extra_context.get('entity_id')
        entity = entity_dict.get(entity_id, missing)
        return actor is not missing and entity is not missing

    for activity in filter(complete, activities):
        activity.actor = user_dict[activity.actor_id]
        entity_id = activity.extra_context['entity_id']
        activity.entity = entity_dict[entity_id]
        love = Love(
            id=activity.object_id, user_id=activity.actor_id,
            entity_id=entity_id, created_at=activity.time
        )
        love.activity = activity
        loves.append(love)

    return loves
