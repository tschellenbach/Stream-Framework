class cassandra::service {
    service { $cassandra::service_name:
        ensure     => running,
        enable     => true,
        hasstatus  => true,
        hasrestart => true,
        subscribe  => Class['cassandra::config'],
        require    => Class['cassandra::config'],
    }
}
