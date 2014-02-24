Metrics
=======
    
Feedly collects metrics regarding feed operations. The default behaviour is to ignore collected metrics rather
than sending them anywhere.

You can configure the metric class with the ``FEEDLY_METRIC_CLASS`` setting and send options as a python dict via
``FEEDLY_METRICS_OPTIONS``


Sending metrics to Statsd
-------------------------

Feedly comes with support for StatsD support, both statsd and python-statsd libraries are supported.

If you use statsd you should use this metric class ``feedly.metrics.statsd.StatsdMetrics`` while if you are
a user of python-statsd you should use ``feedly.metrics.python_statsd.StatsdMetrics``.

The two libraries do the same job and both are suitable for production use.

By default this two classes send metrics to ``localhost`` which is probably not what you want.

In real life you will need something like this

::

    FEEDLY_METRICS_OPTIONS = {
        'host': 'my.statsd.host.tld',
        'port': 8125,
        'prefix': 'feedly'
    }


Custom metric classes
---------------------

If you need to send feedly metrics somewhere you only need to create your own subclass of feedly.metrics.base.Metrics
and configure feedly to use it.
