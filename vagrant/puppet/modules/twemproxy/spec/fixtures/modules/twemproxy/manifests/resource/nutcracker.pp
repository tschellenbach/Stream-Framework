# = Class definition for nutcracker config file
# TODO: Document the class.
define twemproxy::resource::nutcracker (
  $auto_eject_hosts     = true,
  $distribution         = ketama,
  $ensure               = 'present',
  $members              = '',
  $nutcracker_hash      = 'fnv1a_64',
  $redis                = true,
  $server_retry_timeout = '2000',
  $server_failure_limit = '3',
  $statsport            = '22121'
) {

  File {
    owner  => 'root',
    group  => 'root',
    mode   => '0644'
  }

  $ensure_real = $ensure ? {
    'absent' => absent,
    default  => file,
  }

  # Ensure nutcracker config directory exists
  if ! defined(File['/etc/nutcracker']) {
    file { '/etc/nutcracker':
      ensure  => 'directory',
      mode    => '0755',
    }
  }

  # Creates nutcracker config YML combining two templates members and pool.
  file { "/etc/nutcracker/${name}.yml":
    ensure  => "${ensure_real}",
    content => template('twemproxy/pool.erb',
                        'twemproxy/members.erb'),
    notify  => Exec["reload-nutcracker"]
  }

  # Creates nutcracker init for the current pool
  file { "/etc/init.d/${name}":
    ensure  => "${ensure_real}",
    mode    => '0755',
    content => template('twemproxy/nutcracker')
  }

  # Reloads nutcracker if either the init or the config file has change.
  exec { "/etc/init.d/${name} restart":
    command     => "/etc/init.d/${name} restart",
    refreshonly => true,
    alias       => "reload-nutcracker",
    require     => [ File["/etc/init.d/${name}"], File["/etc/nutcracker/${name}"] ]
    
  }
}
