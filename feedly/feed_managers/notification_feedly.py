from feedly.feed_managers.base import Feedly
from feedly.feeds.notification_feed import NotificationFeed
from feedly.utils import warn_on_duplicate
from feedly import tasks as feedly_tasks
import logging

logger = logging.getLogger(__name__)


class NotificationFeedly(Feedly):
    '''
    Manager functionality for interfacing with the 
    Notification feed
    '''
    def add_love(self, love):
        return feedly_tasks.notification_add_love(love)
    
    @warn_on_duplicate
    def _add_love(self, love):
        '''
        We want to write two notifications
        - someone loved your find
        - someone loved your love
        '''
        feeds = []
        activity = love.create_activity()
        
        # send notification about the find
        created_by_id = love.entity.created_by_id
        if love.user_id != created_by_id:
            feed = NotificationFeed(created_by_id)
            activity.extra_context['find'] = True
            logger.info('notifying item finder %s', created_by_id)
            feed.add(activity)
            feeds.append(activity)
            
        # send notification about the love
        if love.user_id != love.influencer_id and love.influencer_id:
            if love.influencer_id != created_by_id:
                logger.info('notifying influencer %s', love.influencer_id)
                feed = NotificationFeed(love.influencer_id)
                activity.extra_context.pop('find', True)
                feed.add(activity)
                feeds.append(feed)
            
        return feeds
    
    def follow(self, follow):
        return feedly_tasks.notification_follow(follow)
    
    @warn_on_duplicate
    def _follow(self, follow):
        '''
        Thierry and 3 other people started following you
        '''
        activity = follow.create_activity()
        feed = NotificationFeed(follow.target_id)
        feed.add(activity)
        return feed
    
    def add_to_list(self, list_item):
        return feedly_tasks.notification_add_to_list(list_item)
    
    @warn_on_duplicate
    def _add_to_list(self, list_item):
        '''
        Guyon added your find to their list back in black
        Guyon and 3 other people added your finds to their lists
        '''
        activity = list_item.create_activity()
        user_id = list_item.list.user_id
        created_by_id = list_item.entity.created_by_id
        if user_id != created_by_id:
            feed = NotificationFeed(created_by_id)
            feed.add(activity)
            return feed
    

