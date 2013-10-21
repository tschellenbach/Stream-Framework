/* The base for all fashiolista servers. Sets up things required by all of our
    servers, e.g. ntp to keep time up to date
*/



class base_server {
    
    $programs = [
      'git-core', 
      'python-pip',
      'python-virtualenv',
      'vim',
      'zsh',
    ]

    # Weird apt::ppa needs this declaration
    class { 'apt':
    }
    
    
    package { $programs: 
        ensure => 'present',
    }

    $pip_packages = [
      'virtualenvwrapper',
    ]

    package { $pip_packages:
        ensure => 'present',
        provider    => 'pip',
        require => Package["python-pip"]
    }

    file { "/etc/gitconfig":
        ensure  => "present",
        source => "puppet:///modules/base_server/gitconfig",
    }
    
    apt::ppa { "ppa:chris-lea/redis-server": }
}
