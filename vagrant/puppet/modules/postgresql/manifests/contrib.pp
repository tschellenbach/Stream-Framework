# Class: postgresql::contrib
#
# This class installs the postgresql contrib package.
#
# Parameters:
#   [*package_name*]    - The name of the postgresql contrib package.
#   [*package_ensure*]  - The ensure value of the package.
#
# Actions:
#
# Requires:
#
# Sample Usage:
#
#   class { 'postgresql::contrib': }
#
class postgresql::contrib (
  $package_name   = $postgresql::params::contrib_package_name,
  $package_ensure = 'present'
) inherits postgresql::params {

  package { 'postgresql-contrib':
    ensure => $package_ensure,
    name   => $package_name,
  }
}
