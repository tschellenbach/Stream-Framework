Puppet-twemproxy
================

This module manages [Twemproxy](http://www.github.com/twitter/twemproxy) package installation from source. It takes into consideration the needed packages depending on the Distro yso you can compile it.

## USAGE
### Creating a pool
<pre>
  twemproxy::resource::nutcracker {
    'pool1':
      ensure    => present,
      members   => [
        {
          ip          => '127.0.0.1',
          name        => 'server1',
          redis_port  => '22121',
          weight      => '1',
        },
        {
          ip         => '127.0.0.1',
          name       => 'server2',
          redis_port => '6662',
          weight     => '1',
        }
      ],
      port       => 22121,
      statsport: => 22122
  }
</pre>

### Creating a resource to monitor
<pre>
twemproxy::resource::monit {
    'twemprodweb':
      country   => es,
      port      => '22114',
      statsport => '21214';
  }
</pre>

## Dependencies

* `puppet-monit`: Ensure monit is installed and configured

## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request
