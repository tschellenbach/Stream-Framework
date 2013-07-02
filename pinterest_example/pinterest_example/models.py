from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    class Meta:
        abstract = True
        

class Item(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    image = models.ImageField()
    source_url = models.TextField()
    

class Board(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField()


class Pin(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    item = models.ForeignKey(Item)
    board = models.ForeignKey(Board)
    influencer = models.ForeignKey(settings.AUTH_USER_MODEL)
    message = models.TextField(blank=True, null=True)
    

class Follow(BaseModel):
    '''
    Simpel mapping between a user and who to follow
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following_set')
    target = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follower_set')
    deleted_at = models.DateTimeField(blank=True, null=True)