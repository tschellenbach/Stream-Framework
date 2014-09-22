

def validate_type_strict(object_, object_types):
    '''
    Validates that object_ is of type object__type
    :param object_: the object to check
    :param object_types: the desired type of the object (or tuple of types)
    '''
    if not isinstance(object_types, tuple):
        object_types = (object_types,)
    exact_type_match = any([type(object_) == t for t in object_types])
    if not exact_type_match:
        error_format = 'Please pass object_ of type %s as the argument, encountered type %s'
        message = error_format % (object_types, type(object_))
        raise ValueError(message)


def validate_list_of_strict(object_list, object_types):
    '''
    Verifies that the items in object_list are of
    type object__type

    :param object_list: the list of objects to check
    :param object_types: the type of the object (or tuple with types)

    In general this goes against Python's duck typing ideology
    See this discussion for instance
    http://stackoverflow.com/questions/1549801/differences-between-isinstance-and-type-in-python

    We use it in cases where you can configure the type of class to use
    And where we should validate that you are infact supplying that class
    '''
    for object_ in object_list:
        validate_type_strict(object_, object_types)
