from feedly.feed_managers.base import Feedly
from feedly.feeds.aggregated_feed import NotificationFeed


class NotificationFeedly(Feedly):
    '''
    Manager functionality for interfacing with the 
    notification feed
    '''
    def add_love(self, love):
        '''
        we want to write two notifications
        - someone loved your find
        - someone loved your love
        '''
        activity = self.create_love_activity(love)
        
        user_ids = [love.created_by_id]
        if love.influencer_id and love.influencer_id != love.created_by_id:
            user_ids.append(love.influencer_id)
        
        feeds = []
        for user_id in user_ids:
            feed = NotificationFeed(user_id)
            feed.append(activity)
            feeds.append(feed)

        return feeds
    
    def create_love_activity(self, love):
        '''
        Store a love in an activity object
        '''
        activity = love.create_activity()
        return activity

