from abc import ABCMeta
from abc import abstractmethod


class StorageBackend:
    '''
    This class works as interface between different different Feedly
    storage backends

    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_content_storage(self, content_type):
        '''
        love_storage = self.get_content_storage(self, Love)
        love_storage = self.get_content_storage(self, 'entity.Love')
        love_storage = self.get_content_storage(self, 'entity_love')
        '''
        pass
