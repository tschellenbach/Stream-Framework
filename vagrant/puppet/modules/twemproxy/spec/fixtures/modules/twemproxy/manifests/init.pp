# = Class: init twemproxy
#
# USAGE:
#  twemproxy::resource::nutcracker {
#    'pool1':
#      ensure    => present,
#      statsport => '22122',
#      members   => [
#        {
#          ip => '127.0.0.1',
#          name   => 'server1',
#          port   => '22121',
#          weight => '1',
#        },
#        {
#          ip     => '127.0.0.1',
#          name   => 'server2',
#          port   => '22122',
#          weight => '1',
#        }
#      ]
#  }

class twemproxy {

  include twemproxy::install

}
