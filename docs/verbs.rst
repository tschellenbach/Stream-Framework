Verbs
=====


Adding new verbs
****************

Registering a new verb is quite easy.
Just subclass the Verb class and give it a unique id.

::


    from stream_framework.verbs import register
    from stream_framework.verbs.base import Verb
    
    
    class Pin(Verb):
        id = 5
        infinitive = 'pin'
        past_tense = 'pinned'
    
    register(Pin)
        
.. seealso:: Make sure your verbs are registered before you read data from stream_framework, if you use django
	you can just define/import them in models.py to make sure they are loaded early

	

Getting verbs
*************

You can retrieve verbs by calling get_verb_by_id.

::

	from stream_framework.verbs import get_verb_by_id
	
	pin_verb = get_verb_by_id(5)