from stream_framework.verbs import register


class Verb(object):

    '''
    Every activity has a verb and an object.
    Nomenclatura is loosly based on
    http://activitystrea.ms/specs/atom/1.0/#activity.summary
    '''
    id = 0

    def __str__(self):
        return self.infinitive

    def serialize(self):
        serialized = self.id
        return serialized


class Follow(Verb):
    id = 1
    infinitive = 'follow'
    past_tense = 'followed'

register(Follow)


class Comment(Verb):
    id = 2
    infinitive = 'comment'
    past_tense = 'commented'

register(Comment)


class Love(Verb):
    id = 3
    infinitive = 'love'
    past_tense = 'loved'

register(Love)


class Add(Verb):
    id = 4
    infinitive = 'add'
    past_tense = 'added'

register(Add)
