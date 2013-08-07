from feedly.verbs import register
from feedly.verbs.base import Verb


class Pin(Verb):
    id = 5
    infinitive = 'pin'
    past_tence = 'pinned'

register(Pin)
