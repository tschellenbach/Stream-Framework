from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'feedly.views',
    url(r'^admin/benchmark/$', 'benchmark', name='feedly_benchmark'),
    url(r'^admin/stats/$', 'stats', name='feedly_stats'),
)

