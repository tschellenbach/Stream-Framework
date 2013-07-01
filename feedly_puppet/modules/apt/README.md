# Apt module for Puppet

## Description
Provides helpful definitions for dealing with Apt.

## Usage

### apt
The apt class provides a number of common resources and options which
are shared by the various defined types in this module. This class
should always be included in your manifests if you are using the `apt`
module.

    class { 'apt':
      always_apt_update    => false,
      disable_keys         => undef,
      proxy_host           => false,
      proxy_port           => '8080',
      purge_sources_list   => false,
      purge_sources_list_d => false,
      purge_preferences_d  => false
    }

### apt::builddep
Install the build depends of a specified package.

    apt::builddep { "glusterfs-server": }

### apt::force
Force a package to be installed from a specific release.  Useful when
using repositories like Debian unstable in Ubuntu.

    apt::force { "glusterfs-server":
	  release => "unstable",
	  version => '3.0.3',
	  require => Apt::Source["debian_unstable"],
    }

### apt::pin
Add an apt pin for a certain release.

    apt::pin { "karmic": priority => 700 }
    apt::pin { "karmic-updates": priority => 700 }
    apt::pin { "karmic-security": priority => 700 }

### apt::ppa
Add a ppa repository using `add-apt-repository`.  Somewhat experimental.

    apt::ppa { "ppa:drizzle-developers/ppa": }

### apt::release
Set the default apt release.  Useful when using repositories like
Debian unstable in Ubuntu.

    apt::release { "karmic": }

### apt::source
Add an apt source to `/etc/apt/sources.list.d/`.

    apt::source { "debian_unstable":
      location          => "http://debian.mirror.iweb.ca/debian/",
      release           => "unstable",
      repos             => "main contrib non-free",
      required_packages => "debian-keyring debian-archive-keyring",
      key               => "55BE302B",
      key_server        => "subkeys.pgp.net",
      pin               => "-10",
      include_src       => true
    }

This source will configure your system for the Puppet Labs APT
repository.

    apt::source { 'puppetlabs':
      location   => 'http://apt.puppetlabs.com',
      repos      => 'main',
      key        => '4BD6EC30',
      key_server => 'pgp.mit.edu',
    }

### apt::key
Add a key to the list of keys used by apt to authenticate packages.

    apt::key { "puppetlabs":
      key        => "4BD6EC30",
      key_server => "pgp.mit.edu",
    }

    apt::key { "jenkins":
      key        => "D50582E6",
      key_source => "http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key",
    }

Note that use of the "key_source" parameter requires wget to be
installed and working.


## Contributors
A lot of great people have contributed to this module. A somewhat
current list follows.

Ben Godfrey <ben.godfrey@wonga.com>
Branan Purvine-Riley <branan@puppetlabs.com>
Christian G. Warden <cwarden@xerus.org>  
Dan Bode <bodepd@gmail.com> <dan@puppetlabs.com>  
Garrett Honeycutt <github@garretthoneycutt.com>  
Jeff Wallace <jeff@evolvingweb.ca> <jeff@tjwallace.ca>  
Ken Barber <ken@bob.sh>  
Matthaus Litteken <matthaus@puppetlabs.com> <mlitteken@gmail.com>  
Matthias Pigulla <mp@webfactory.de>  
Monty Taylor <mordred@inaugust.com>  
Peter Drake <pdrake@allplayers.com>  
Reid Vandewiele <marut@cat.pdx.edu>  
Robert Navarro <rnavarro@phiivo.com>  
Ryan Coleman <ryan@puppetlabs.com>  
Scott McLeod <scott.mcleod@theice.com>  
Spencer Krum <spencer@puppetlabs.com>  
William Van Hevelingen <blkperl@cat.pdx.edu> <wvan13@gmail.com>  
Zach Leslie <zach@puppetlabs.com>  
