

VERB_DICT = dict()


def register(verb):
    '''
    Registers the given verb class
    '''
    from feedly.verbs.base import Verb
    if not issubclass(verb, Verb):
        raise ValueError('%s doesnt subclass Verb' % verb)
    registered_verb = VERB_DICT.get(verb.id, verb)
    if registered_verb != verb:
        raise ValueError(
            'cant register verb %r with id %s (clashing with verb %r)' %
            (verb, verb.id, registered_verb))
    VERB_DICT[verb.id] = verb


def get_verb_by_id(verb_id):
    if not isinstance(verb_id, int):
        raise ValueError('please provide a verb id, got %r' % verb_id)

    return VERB_DICT[verb_id]
