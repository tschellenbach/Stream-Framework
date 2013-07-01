class oh_my_zsh {
  
  
}

define oh_my_zsh::install($path = '/usr/bin/zsh') {

  if(!defined(Package['git-core'])) {
    package { 'git-core':
      ensure => present,
    }
  }

  exec { "chsh -s $path $name":
    path    => '/bin:/usr/bin',
    unless  => "grep -E '^${name}.+:${$path}$' /etc/passwd",
    require => Package['zsh']
  }

  if(!defined(Package['curl'])) {
    package { 'curl':
      ensure => present,
    }
  }

  file { '/home/vagrant/.zshrc':
    source    => "puppet:///modules/oh_my_zsh/zshrc",
    ensure => 'file',
    require => Exec['clone_oh_my_zsh'],
  }

  exec { 'clone_oh_my_zsh':
    path    => '/bin:/usr/bin',
    cwd     => "/home/$name",
    user    => $name,
    command => "git clone http://github.com/breidh/oh-my-zsh.git /home/$name/.oh-my-zsh",
    creates => "/home/$name/.oh-my-zsh",
    require => [Package['git-core'], Package['zsh'], Package['curl']]
  }

}


