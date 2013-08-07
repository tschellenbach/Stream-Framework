class cassandra::install {
    package { 'dsc':
        ensure => $cassandra::version,
        name   => $cassandra::package_name,
    }

    $python_cql_name = $::osfamily ? {
        'Debian'    => 'python-cql',
        'RedHat'    => 'python26-cql',
        default     => 'python-cql',
    }

    package { $python_cql_name:
        ensure => installed,
    }

    if ($::osfamily == 'Debian') {
        file { 'CASSANDRA-2356 /etc/cassandra':
            ensure => directory,
            path   => '/etc/cassandra',
            owner  => 'root',
            group  => 'root',
            mode   => '0755',
        }

        exec { 'CASSANDRA-2356 Workaround':
            path    => ['/sbin', '/bin', '/usr/sbin', '/usr/bin'],
            command => '/etc/init.d/cassandra stop && rm -rf /var/lib/cassandra/*',
            creates => '/etc/cassandra/CASSANDRA-2356',
            user    => 'root',
            require => [
                    Package['dsc'],
                    File['CASSANDRA-2356 /etc/cassandra'],
                ],
        }

        file { 'CASSANDRA-2356 marker file':
            ensure  => file,
            path    => '/etc/cassandra/CASSANDRA-2356',
            owner   => 'root',
            group   => 'root',
            mode    => '0644',
            content => '# Workaround for CASSANDRA-2356',
            require => [
                    File['CASSANDRA-2356 /etc/cassandra'],
                    Exec['CASSANDRA-2356 Workaround'],
                ],
        }
    }
}
