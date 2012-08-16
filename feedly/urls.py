from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'feedly.views',
    url(r'^admin/benchmark/$', 'benchmark', name='feedly_benchmark'),
    url(r'^admin/monitor/$', 'monitor', name='feedly_monitor'),
    url(r'^admin/$', 'index', name='feedly_index'),
)

