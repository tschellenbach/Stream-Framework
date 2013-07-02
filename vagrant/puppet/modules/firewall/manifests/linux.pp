class firewall::linux (
  $ensure = running
) {
  $enable = $ensure ? {
    running => true,
    stopped => false,
  }

  package { 'iptables':
    ensure => present,
  }

  case $::operatingsystem {
    'RedHat', 'CentOS', 'Fedora': {
      class { "${title}::redhat":
        ensure  => $ensure,
        enable  => $enable,
        require => Package['iptables'],
      }
    }
    'Debian', 'Ubuntu': {
      class { "${title}::debian":
        ensure  => $ensure,
        enable  => $enable,
        require => Package['iptables'],
      }
    }
    'Archlinux': {
      class { "${title}::archlinux":
        ensure  => $ensure,
        enable  => $enable,
        require => Package['iptables'],
      }
    }
    default: {}
  }
}
