The activity model
==================


Extend the activity model
*************************


Adding new verbs
****************

Registering a new verb is quite easy.
Just subclass the Verb class and give it a unique id.

::


    from feedly.verbs import register
    from feedly.verbs.base import Verb
    
    
    class Pin(Verb):
        id = 5
        infinitive = 'pin'
        past_tense = 'pinned'
    
    register(Pin)
        
.. seealso:: Make sure your verbs are registered before you read data from feedly, if you use django
you can just define/import them in models.py to make sure they are loaded early


Activity serialization
**********************


Activity order and uniqueness
*****************************


Aggregated activities
*********************

