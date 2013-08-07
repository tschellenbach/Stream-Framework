



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

class { 'java': }

class { 'cassandra':
    cluster_name  => 'Feedly',
    seeds         => [ '192.168.1.50', ],
}