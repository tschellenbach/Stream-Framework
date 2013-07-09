from feedly.feed_managers.base import Feedly


class LoveFeedly(Feedly):

    def create_love_activity(self, love):
        activity = love.create_activity()
        return activity

    def add_love(self, love):
        activity = self.create_love_activity(love)
        self.add_user_activity(love.user_id, activity)

    def remove_love(self, love):
        activity = self.create_love_activity(love)
        self.remove_user_activity(love.user_id, activity)

    def get_user_follower_ids(self, user):
        profile = user.get_profile()
        following_ids = profile.cached_follower_ids()
        return following_ids
