# = Class for Twemproxy installation
# TODO: Document the installation
class twemproxy::install (
  $version        = '0.2.4',
  $prefix         = '/usr/local',
  $debug_mode     = true,
  $debug_opts     = 'full',
  $cflags         = true,
  $cflags_opts    = '-ggdb3 -O0'
  ) {

  # Ensure /usr/local/src diretory exists
  if ! defined(File["${prefix}/src"]) {
    file { "${prefix}/src": ensure  => 'directory' }
  }

  # Get the twemproxy package from puppet fileserver
  # I decided that in order to maintain security this
  # package must be in puppet masters control.
  file { "${prefix}/src/nutcracker-${version}.tar.gz":
    source  => "puppet:///modules/twemproxy/nutcracker-${version}.tar.gz",
    alias   => 'nutcracker-source-tgz',
    before  => Exec['untar-nutcracker-source']
  }
  

  # Untar the nutcracker file.
  exec { "tar xzf nutcracker-${version}.tar.gz":
    path => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    cwd       => "/usr/local/src",
    creates   => "/usr/local/src/nutcracker-${version}",
    alias     => "untar-nutcracker-source",
    subscribe => File["nutcracker-source-tgz"]
  }

  # If debug and cflags are true, compile in debug mode
  # in other case compile it without debug.
  if ($debug == true or $cflags == true){
    exec { "/bin/ls | export CFLAGS=\"${cflags_opts}\"; ./configure --enable-debug=\"${debug_opts}\"":
      path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
      cwd     => "${prefix}/src/nutcracker-${version}",
      require => Exec['untar-nutcracker-source'],
      creates => "${prefix}/src/nutcracker-${version}/config.h",
      alias   => "configure-nutcracker",
      before  => Exec["make install"]
    }
  }
  else {

    notice ('Compiling Twemproxy without CFLAGS or DEBUG mode.')

    exec { "sh configure":
      path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
      cwd     => "${prefix}/src/nutcracker-${version}",
      require => Exec['untar-nutcracker-source'],
      creates => "${prefix}/src/nutcracker-${version}/config.h",
      alias   => "configure-nutcracker",
      before  => Exec["make install"]
    }
  }

  # Isn't if obvious? make install ;) 
  exec { "make && make install":
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    cwd     => "/usr/local/src/nutcracker-${version}",
    alias   => "make install",
    creates => [ "${prefix}/src/nutcracker-${version}/src/nutcracker",
                 "${prefix}/sbin/nutcracker" ],
    require => Exec["configure-nutcracker"],
  }

}
