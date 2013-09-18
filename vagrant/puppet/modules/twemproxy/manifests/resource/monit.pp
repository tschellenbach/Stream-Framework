# define: twemproxy::resource::monit
#
# Definition for twemproxy nodes
#
# Parameters:
# [*ensure*] - Enables or disables Redis nodes (present|absent)
# [*members*] - Array of Redis servers
#
# Actions:
#
# Requires:
#
# Sample Usage:

define twemproxy::resource::monit (
  $domain = 'example.com',
  $ensure = 'present',
  $port,
  $statsport
) {
  File {
    owner => root,
    group => root,
    mode  => '0644',
  }

  file { "/etc/monit/conf.d/nutcracker-${name}.conf":
      ensure  => $ensure ? {
        'absent' => absent,
        default  => 'file',
      },
      owner   => root,
      group   => root,
      mode    => '0755',
      content => template('twemproxy/monit.erb'),
      notify  => Exec["monit-${name}"];
  }

  exec { "monit-${name}":
    command       => '/etc/init.d/monit restart',
    refreshonly   => true;
  }
}
