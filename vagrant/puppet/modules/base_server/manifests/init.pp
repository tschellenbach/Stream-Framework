/* The base for all fashiolista servers. Sets up things required by all of our
    servers, e.g. ntp to keep time up to date
*/

class base_server {

    #exec { 'apt-get-update':
    #    command => "/usr/bin/apt-get update",
    #    onlyif => "/bin/bash -c 'exit $(( $(( $(date +%s) - $(stat -c %Y /var/lib/apt/lists/$( ls /var/lib/apt/lists/ -tr1|tail -1 )) )) <= 604800 ))'"
    #}
    
    # hack to make it run only once
    exec { 'apt-get-update':
        command => "/usr/bin/apt-get update > /home/vagrant/apt-update-done",
        unless => "/bin/ls /home/vagrant/apt-update-done",
    }
    
    $programs = [
      'ntp', 
      'screen', 
      'autossh', 
      'git-core', 
      'vim', 
      'zsh', 
      'python-pip',
      'python-virtualenv', 
      'htop', 
      'mc', 
      'sysstat', 
      'iotop', 
      'tmux',
      'nmon', 
      'aptitude',
    ]

    package { $programs: 
        ensure => 'present',
        require => Exec["apt-get-update"]
    }

    $pip_packages = [
      'legit', 
      'boto', 
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


}
