class sudoers {
    file { "sudoers-file":
        source  => "puppet:///modules/sudoers/sudoers",
        ensure  => "present",
        path    => "/etc/sudoers",
        owner   => "root",
        group   => "root",
        mode    => 440
    }
}
