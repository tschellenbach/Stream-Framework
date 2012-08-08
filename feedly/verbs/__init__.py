

VERB_DICT = dict()


def register(verb):
    VERB_DICT[verb.id] = verb


def get_verb_by_id(verb_id):
    if not isinstance(verb_id, int):
        raise ValueError('please provide a verb id, got %r' % verb_id)
    
    return VERB_DICT[verb_id]
