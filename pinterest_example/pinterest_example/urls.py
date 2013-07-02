from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
                       # Examples:
                       url(r'^$', 'pinterest_example.views.homepage',
                           name='homepage'),
                       # the two feed pages
                       url(r'^feed/$',
                           'pinterest_example.views.feed', name='feed'),
                       url(r'^trending/$',
                           'pinterest_example.views.trending', name='trending'),
                       # a page showing the users profile
                       url(r'^profile/(?P<username>[\w_-]+)/$',
                           'pinterest_example.views.profile', name='profile'),
                       # backends for follow and pin
                       url(r'^pin/$',
                           'pinterest_example.views.pin', name='pin'),
                       url(r'^follow/$',
                           'pinterest_example.views.follow', name='follow'),
                       # url(r'^blog/', include('blog.urls')),

                       url(r'^admin/', include(admin.site.urls)),
                       )

if settings.DEBUG:
    urlpatterns = patterns('',
                           url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
                               {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                           url(r'', include(
                               'django.contrib.staticfiles.urls')),
                           ) + urlpatterns
