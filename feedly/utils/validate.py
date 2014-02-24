

def validate_type(object_, object__type):
    if not isinstance(object_, object__type):
        error_format = 'Please pass object_ of type %s as the argument, encountered type %s'
        message = error_format % (object__type, type(object_))
        raise ValueError(message)


def validate_list_of(object_list, object__type):
    for object_ in object_list:
        validate_type(object_, object__type)
