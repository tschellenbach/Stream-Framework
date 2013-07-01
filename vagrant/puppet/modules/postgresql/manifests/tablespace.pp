# Define: postgresql::tablespace
#
# This module creates tablespace
#
# Parameters:
#   [*title*]       - the name of a tablespace to be created. The name cannot begin with pg_, as such names are reserved for system tablespaces.
#   [*owner*]       - the name of the user who will own the tablespace. If omitted, defaults to the user executing the command.
#                     Only superusers can create tablespaces, but they can assign ownership of tablespaces to non-superusers.
#   [*location*]    - The directory that will be used for the tablespace. The directory should be empty and must be owned by the PostgreSQL
#                     system user. The directory must be specified by an absolute path name.
#
# Actions:
#
# Requires:
#
#   class postgresql::server
#
# Sample Usage:
#
#  postgresql::tablespace { 'dbspace':
#    location => '/data/dbs',
#  }
#
#
define postgresql::tablespace(
  $location,
  $owner = undef,
  $spcname  = $title)
{
  include postgresql::params

  Postgresql_psql {
    psql_user    => $postgresql::params::user,
    psql_group   => $postgresql::params::group,
    psql_path    => $postgresql::params::psql_path,
  }

  if ($owner == undef) {
    $owner_section = ''
  }
  else {
    $owner_section = "OWNER \"${owner}\""
  }

  $create_tablespace_command = "CREATE TABLESPACE \"${spcname}\" ${owner_section} LOCATION '${location}'"

  file { $location:
    ensure => directory,
    owner  => $postgresql::params::user,
    group  => $postgresql::params::group,
    mode   => '0700',
  }

  postgresql_psql { "Create tablespace '${spcname}'":
    command => $create_tablespace_command,
    unless  => "SELECT spcname FROM pg_tablespace WHERE spcname='${spcname}'",
    require => [Class['postgresql::server'], File[$location]],
  }
}
