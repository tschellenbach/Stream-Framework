from stream_framework.utils import get_class_from_string


VERB_DICT = dict()


def get_verb_storage():
    from stream_framework import settings
    if settings.STREAM_VERB_STORAGE == 'in-memory':
        return VERB_DICT
    else:
        return get_class_from_string(settings.STREAM_VERB_STORAGE)()


def register(verb):
    '''
    Registers the given verb class
    '''
    from stream_framework.verbs.base import Verb
    if not issubclass(verb, Verb):
        raise ValueError('%s doesnt subclass Verb' % verb)
    registered_verb = get_verb_storage().get(verb.id, verb)
    if registered_verb != verb:
        raise ValueError(
            'cant register verb %r with id %s (clashing with verb %r)' %
            (verb, verb.id, registered_verb))
    get_verb_storage()[verb.id] = verb


def get_verb_by_id(verb_id):
    if not isinstance(verb_id, int):
        raise ValueError('please provide a verb id, got %r' % verb_id)

    return get_verb_storage()[verb_id]
