# ppa.pp

define apt::ppa(
  $release = $::lsbdistcodename
) {
  include apt::params
  include apt::update

  $sources_list_d = $apt::params::sources_list_d

  if ! $release {
    fail('lsbdistcodename fact not available: release parameter required')
  }

  $filename_without_slashes = regsubst($name, '/', '-', G)
  $filename_without_dots    = regsubst($filename_without_slashes, '\.', '_', G)
  $filename_without_ppa     = regsubst($filename_without_dots, '^ppa:', '', G)
  $sources_list_d_filename  = "${filename_without_ppa}-${release}.list"
  
  $package = $::lsbdistrelease ? {
	  /^[1-9]\..*|1[01]\..*|12.04$/ => 'python-software-properties',
	  default  => 'software-properties-common',
  }
  
  if ! defined(Package[$package]) {
    package { $package: }
  }

  exec { "add-apt-repository-${name}":
    command   => "/usr/bin/add-apt-repository ${name}",
    creates   => "${sources_list_d}/${sources_list_d_filename}",
    logoutput => 'on_failure',
    require   => [
      File[$sources_list_d],
      Package["${package}"],
    ],
    notify    => Exec['apt_update'],
  }

  file { "${sources_list_d}/${sources_list_d_filename}":
    ensure  => file,
    require => Exec["add-apt-repository-${name}"],
  }

  # Need anchor to provide containment for dependencies.
  anchor { "apt::ppa::${name}":
    require => Class['apt::update'],
  }
}
