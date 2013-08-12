# Class: postgresql::server
#
# == Class: postgresql::server
# Manages the installation of the postgresql server.  manages the package and
# service.
#
# === Parameters:
# [*package_name*] - name of package
# [*service_name*] - name of service
#
# Configuration:
#   Advanced configuration setting parameters can be placed into 'postgresql_puppet_extras.conf' (located in the same
#   folder as 'postgresql.conf'). You can manage that file as a normal puppet file resource, or however you see fit;
#   which gives you complete control over the settings. Any value you specify in that file will override any existing
#   value set in the templated version.
#
# Actions:
#
# Requires:
#
# Sample Usage:
#
class postgresql::server (
  $package_name     = $postgresql::params::server_package_name,
  $package_ensure   = 'present',
  $service_name     = $postgresql::params::service_name,
  $service_provider = $postgresql::params::service_provider,
  $service_status   = $postgresql::params::service_status,
  $config_hash      = {}
) inherits postgresql::params {

  package { 'postgresql-server':
    ensure  => $package_ensure,
    name    => $package_name,
    tag     => 'postgresql',
  }

  $config_class = {
    'postgresql::config' => $config_hash,
  }

  create_resources( 'class', $config_class )


  service { 'postgresqld':
    ensure    => running,
    name      => $service_name,
    enable    => true,
    require   => Package['postgresql-server'],
    provider  => $service_provider,
    hasstatus => true,
    status    => $service_status,
  }

  if ($postgresql::params::needs_initdb) {
    include postgresql::initdb

    Package['postgresql-server'] -> Class['postgresql::initdb'] -> Class['postgresql::config'] -> Service['postgresqld']
  }
  else  {
    Package['postgresql-server'] -> Class['postgresql::config'] -> Service['postgresqld']
  }

  exec { 'reload_postgresql':
    path        => '/usr/bin:/usr/sbin:/bin:/sbin',
    command     => "service ${service_name} reload",
    onlyif      => $service_status,
    refreshonly => true,
  }
}
