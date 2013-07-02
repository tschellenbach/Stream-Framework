class local_dev::pil {
    notice('setting up libs for PIL')
    # required for PIL
    apt::builddep { "python-imaging": 
      require => Exec["apt-get-update"]
    }

    # PIL requirements
    package { "libjpeg8":
        ensure  => "latest",
    }
    package { "libjpeg-dev":
        ensure  => "latest",
    }
    package { "libfreetype6":
        ensure  => "latest",
    }
    package { "zlib1g-dev":
        ensure  => "latest",
    }

    # Ubuntu installs the libjpeg files in a different location to that expected by PIL, so
    # we use these symlinks to make sure PIL can access the libraries.
    file { "/usr/lib/libjpeg.so":
        ensure  => "link",
        target  => "/usr/lib/x86_64-linux-gnu/libjpeg.so",
        require => Package["libjpeg8"],
    }
    file { "/usr/lib/libfreetype.so":
        ensure  => "link",
        target  => "/usr/lib/x86_64-linux-gnu/libfreetype.so",
        require => Package["libfreetype6"],
    }
    file { "/usr/lib/libz.so":
        ensure  => "link",
        target  => "/usr/lib/x86_64-linux-gnu/libz.so",
        require => Package["zlib1g-dev"],
    }
    # End PIL requirements
}


class java() {
  # based on http://linuxg.net/how-to-install-oracle-java-jdk-678-on-ubuntu-13-04-12-10-12-04/
  # and http://architects.dzone.com/articles/puppet-installing-oracle-java

  exec {"apt_update_initial":
    command => '/usr/bin/apt-get update',
  }

  package { "python-software-properties": 
    require => Exec["apt_update_initial"],
  }
 
  exec { "add-apt-repository-oracle":
    command => "/usr/bin/add-apt-repository -y ppa:webupd8team/java",
    notify => Exec["apt_update"],
    require => Package["python-software-properties"]
  }

  exec {"java_apt_update":
    command => '/usr/bin/apt-get update',
    refreshonly => 'true'
  }

  exec {
    'set-licence-selected':
      command => '/bin/echo debconf shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections';
 
    'set-licence-seen':
      command => '/bin/echo debconf shared/accepted-oracle-license-v1-1 seen true | /usr/bin/debconf-set-selections';
  }
 
  package { 'oracle-java6-installer':
    require => [Exec['java_apt_update'], Exec['add-apt-repository-oracle'], Exec['set-licence-selected'], Exec['set-licence-seen']],
  }
}



class local_dev::requirements {
	  notice('setting up our local dev server requirements')
	
    # easy shortcut for running puppet locally
    file { "/usr/bin/local-puppet":
        source    => "puppet:///modules/local_dev/local_puppet.sh",
        ensure  => 'file',
    }

    file { "/home/vagrant/Envs":
        ensure  => 'directory',
        owner => 'vagrant',
    }
    
    oh_my_zsh::install { 'vagrant':}

    package { ["memcached"]:
      ensure => 'present'
    }

    service { "memcached":
      ensure  => "running",
      enable  => "true",
      require => Package["memcached"],
    }
}

class local_dev::psyco {
    package { ["libpq-dev", 'python-dev']:
        ensure  => "latest",
    }
    
    # This package is needed for the python one to install properly
    package { "python-psycopg2":
        ensure  => "latest",
    }
    
}


class local_dev {
    require local_dev::requirements
    require local_dev::pil
    require nginx
    require local_dev::psyco
    class { 'java': }

    class { 'cassandra':
        cluster_name  => 'Feedly',
        seeds         => [ '192.168.1.50', ],
    }
    
    class { 'postgresql::server': }
    notice('setting up the virtual env')
    
    # time to setup a virtual env
    /*
    exec {"create-virtualenv":
        user => 'vagrant',
        command => "/usr/bin/virtualenv /home/vagrant/Envs/local_dev",
        unless  => "/bin/ls /home/vagrant/Envs/local_dev",
        require => File["/home/vagrant/Envs"],
        logoutput => true,
    }
    #too slow to run via puppet
    exec {"install-requirements":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/pip install --use-mirrors -r /vagrant/requirements/development.txt",
        require => Exec["create-virtualenv"],
        logoutput => true,
        timeout => 600,
    }
    
    # run syncdb after we are sure we have the latest version of django facebook
    exec {"syncdb":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/python /vagrant/manage.py syncdb --all --noinput",
        logoutput => true,
        require => Exec["install-requirements"],
    }
    */

}
