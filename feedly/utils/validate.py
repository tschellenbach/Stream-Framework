

def validate_type_strict(object_, object__type):
    '''
    Validates that object_ is of type object__type
    :param object_: the object to check
    :param object__type: the desired type of the object
    '''
    if not isinstance(object_, object__type) or type(object_) != object__type:
        error_format = 'Please pass object_ of type %s as the argument, encountered type %s'
        message = error_format % (object__type, type(object_))
        raise ValueError(message)


def validate_list_of_strict(object_list, object__type):
    '''
    Verifies that the items in object_list are of
    type object__type

    :param object_list: the list of objects to check
    :param object__type: the type of the object

    In general this goes against Python's duck typing ideology
    See this discussion for instance
    http://stackoverflow.com/questions/1549801/differences-between-isinstance-and-type-in-python

    We use it in cases where you can configure the type of class to use
    And where we should validate that you are infact supplying that class
    '''
    for object_ in object_list:
        validate_type_strict(object_, object__type)
