# Class: postgresql::python
# This class installs the python libs for postgresql.
#
# Parameters:
#   [*ensure*]       - ensure state for package.
#                        can be specified as version.
#   [*package_name*] - name of package
class postgresql::python(
  $package_name   = $postgresql::params::python_package_name,
  $package_ensure = 'present'
) inherits postgresql::params {

  package { 'python-psycopg2':
    ensure => $package_ensure,
    name   => $package_name,
  }

}
