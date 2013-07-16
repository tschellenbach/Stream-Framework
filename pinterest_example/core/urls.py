from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'core.views.homepage',
                           name='homepage'),
                       # the three feed pages
                       url(r'^feed/$',
                           'core.views.feed', name='feed'),
                       url(r'^aggregated_feed/$',
                           'core.views.aggregated_feed', name='aggregated_feed'),
                       url(r'^trending/$',
                           'core.views.trending', name='trending'),
                       # a page showing the users profile
                       url(r'^profile/(?P<username>[\w_-]+)/$',
                           'core.views.profile', name='profile'),
                       # backends for follow and pin
                       url(r'^pin/$',
                           'core.views.pin', name='pin'),
                       url(r'^follow/$',
                           'core.views.follow', name='follow'),
                       # the admin
                       url(r'^admin/', include(admin.site.urls)),
                       )

if settings.DEBUG:
    urlpatterns = patterns('',
                           url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           url(r'', include(
                               'django.contrib.staticfiles.urls')),
                           ) + urlpatterns

# make sure we register verbs when django starts
from core import verbs
