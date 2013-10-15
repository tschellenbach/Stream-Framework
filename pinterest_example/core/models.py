from django.db import models
from django.conf import settings
from django.utils.timezone import make_naive
import pytz


class BaseModel(models.Model):

    class Meta:
        abstract = True


class Item(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    image = models.ImageField(upload_to='items')
    source_url = models.TextField()
    message = models.TextField(blank=True, null=True)
    pin_count = models.IntegerField(default=0)

    # class Meta:
    #    db_table = 'pinterest_example_item'


class Board(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField()


class Pin(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    item = models.ForeignKey(Item)
    board = models.ForeignKey(Board)
    influencer = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='influenced_pins')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def create_activity(self):
        from feedly.activity import Activity
        from core.verbs import Pin as PinVerb
        activity = Activity(
            self.user_id,
            PinVerb,
            self.id,
            self.influencer_id,
            time=make_naive(self.created_at, pytz.utc),
            extra_context=dict(item_id=self.item_id)
        )
        return activity


class Follow(BaseModel):

    '''
    Simpel mapping between a user and who to follow
    '''
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='following_set')
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='follower_set')
    deleted_at = models.DateTimeField(blank=True, null=True)


from core import verbs
