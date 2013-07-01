# Class: postgresql::client
#
#   This class installs postgresql client software.
#
#   *Note* don't forget to make sure to add any necessary yum or apt
#   repositories if specifying a custom version.
#
# Parameters:
#   [*package_name*]  - The name of the postgresql client package.
#   [*ensure*] - the ensure parameter passed to the postgresql client package resource
# Actions:
#
# Requires:
#
# Sample Usage:
#
class postgresql::client (
  $package_name   = $postgresql::params::client_package_name,
  $package_ensure = 'present'
) inherits postgresql::params {

  package { 'postgresql-client':
    ensure  => $package_ensure,
    name    => $package_name,
    tag     => 'postgresql',
  }

}
