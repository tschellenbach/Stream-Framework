from feedly.feed_managers.base import Feedly
from feedly.feeds.notification_feed import NotificationFeed


class NotificationFeedly(Feedly):
    '''
    Manager functionality for interfacing with the 
    Notification feed
    '''
    def add_love(self, love):
        '''
        We want to write two notifications
        - someone loved your find
        - someone loved your love
        '''
        activity = love.create_activity()
        
        created_by_id = love.entity.created_by_id
        user_ids = [created_by_id]
        
        if love.influencer_id and love.influencer_id != created_by_id:
            user_ids.append(love.influencer_id)
            
        #don't send notifications about your own love :)
        user_ids = [uid for uid in user_ids if uid != love.user_id]
        
        feeds = []
        for user_id in user_ids:
            feed = NotificationFeed(user_id)
            feed.add(activity)
            feeds.append(feed)

        return feeds
    
    def follow(self, follow):
        '''
        Thierry and 3 other people started following you
        '''
        activity = follow.create_activity()
        feed = NotificationFeed(follow.target_id)
        feed.add(activity)
        return feed
    
    def add_to_list(self, list_item):
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
    

