import datetime

FEED_END = '===end==='


class FeedEndMarker(object):

    def __init__(self):
        # My date of birth is before any Fashiolista loves
        self.time = datetime.datetime(1986, 11, 30)

    def serialize(self):
        serialized = FEED_END
        return serialized

    @property
    def serialization_id(self):
        return self.serialize()
