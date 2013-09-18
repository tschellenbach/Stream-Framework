class local_dev::pil {
    notice('setting up libs for PIL')
    # required for PIL
    apt::builddep { "python-imaging": 
    }

}

class local_dev::compass {
    # Ensure we have ruby
    package { "ruby":
        ensure => latest,
    }

    # Ensure we can install gems
    package { 'rubygems':
        ensure => 'latest'
    }

    # Install gems
    package { 'compass':
        provider => 'gem',
        ensure => 'latest'
    }
}


class java() {
  # based on http://linuxg.net/how-to-install-oracle-java-jdk-678-on-ubuntu-13-04-12-10-12-04/
  # and http://architects.dzone.com/articles/puppet-installing-oracle-java

  #exec {"apt_update_initial":
  #  command => '/usr/bin/apt-get update',
  #}

  package { "python-software-properties": 
    #require => Exec["apt_update_initial"],
  }
 
  exec { "add-apt-repository-oracle":
    command => "/usr/bin/add-apt-repository -y ppa:webupd8team/java",
    notify => Exec["java_apt_update"],
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
 
  package { 'oracle-java7-installer':
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

}

class local_dev {
    require local_dev::requirements
    require local_dev::pil
    require local_dev::compass
    
    class { 'java': }

    class { 'cassandra':
        cluster_name  => 'Feedly',
        start_native_transport => 'true',
        seeds         => [ '10.0.2.15', ],
    }
    
    notice('setting up the virtual env')
    
    package { 'redis-server': 
        ensure => '2:2.6.16-1chl1~precise1',
        require => Apt::Ppa['ppa:chris-lea/redis-server']
    }
    
    twemproxy::resource::nutcracker {
        'pool1':
          ensure    => present,
          members   => [
            {
              ip          => '127.0.0.1',
              name        => 'server1',
              redis_port  => '6379',
            },
          ],
          port       => 22122
    }
    
    # time to setup a virtual env
    exec {"create-virtualenv":
        user => 'vagrant',
        command => "/usr/bin/virtualenv /home/vagrant/Envs/local_dev",
        unless  => "/bin/ls /home/vagrant/Envs/local_dev",
        require => File["/home/vagrant/Envs"],
        logoutput => true,
    }

    exec {"distribute":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/pip install distribute==0.7.3",
        require => [Exec["create-virtualenv"], Package["python-pip"]],
        logoutput => true,
        timeout => 600,
    }

    #too slow to run via puppet
    exec {"install-requirements":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/pip install --use-mirrors -r /vagrant/pinterest_example/requirements/development.txt",
        require => Exec["distribute"],
        logoutput => true,
        timeout => 600,
    }
    
    # make sure feedly is in editable mode
    exec {"install-feedly":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/pip install -e /vagrant",
        require => Exec["install-requirements"],
        logoutput => true,
        timeout => 600,
    }
    
    # run syncdb after we are sure we have the latest version of django facebook
    exec {"syncdb":
        user => 'vagrant',
        command => "/home/vagrant/Envs/local_dev/bin/python /vagrant/pinterest_example/manage.py syncdb --all --noinput",
        logoutput => true,
        require => Exec["install-feedly"],
    }

}
