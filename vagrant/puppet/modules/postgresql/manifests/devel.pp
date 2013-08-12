# Class: postgresql::devel
#
#   This class installs postgresql development libraries
#
# Parameters:
#   [*package_name*]   - The name of the postgresql development package.
#   [*package_ensure*] - The ensure value of the package
#
# Actions:
#
# Requires:
#
# Sample Usage:
#
class postgresql::devel(
  $package_name   = $postgresql::params::devel_package_name,
  $package_ensure = 'present'
) inherits postgresql::params {

  package { 'postgresql-devel':
    ensure => $package_ensure,
    name   => $package_name,
    tag    => 'postgresql',
  }
}
