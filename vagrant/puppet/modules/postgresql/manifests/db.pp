# Define: postgresql::db
#
# This module creates database instances, a user, and grants that user
# privileges to the database.
#
# Since it requires class postgresql::server, we assume to run all commands as the
# postgresql user against the local postgresql server.
#
# TODO: support an array of privileges for "grant"; currently only supports a single
#  privilege, which is pretty useless unless that privilege is "ALL"
#
# Parameters:
#   [*title*]       - postgresql database name.
#   [*user*]        - username to create and grant access.
#   [*password*]    - user's password.  may be md5-encoded, in the format returned by the "postgresql_password"
#                            function in this module
#   [*charset*]     - database charset. defaults to 'utf8'
#   [*grant*]       - privilege to grant user. defaults to 'all'.
#   [*tablespace*]  - database tablespace. default to use the template database's tablespace.
#   [*locale*]      - locale for database. defaults to 'undef' (effectively 'C').
#
# Actions:
#
# Requires:
#
#   class postgresql::server
#
# Sample Usage:
#
#  postgresql::db { 'mydb':
#    user     => 'my_user',
#    password => 'password',
#    grant    => 'all'
#  }
#
define postgresql::db (
  $user,
  $password,
  $charset     = $postgresql::params::charset,
  $locale      = $postgresql::params::locale,
  $grant       = 'ALL',
  $tablespace = undef
) {
  include postgresql::params

  postgresql::database { $name:
    # TODO: ensure is not yet supported
    #ensure     => present,
    charset     => $charset,
    tablespace  => $tablespace,
    #provider   => 'postgresql',
    require     => Class['postgresql::server'],
    locale      => $locale,
  }

  if ! defined(Postgresql::Database_user[$user]) {
    postgresql::database_user { $user:
      # TODO: ensure is not yet supported
      #ensure         => present,
      password_hash   => $password,
      #provider       => 'postgresql',
      require         => Postgresql::Database[$name],
    }
  }

  postgresql::database_grant { "GRANT ${user} - ${grant} - ${name}":
    privilege       => $grant,
    db              => $name,
    role            => $user,
    #provider       => 'postgresql',
    require         => [Postgresql::Database[$name], Postgresql::Database_user[$user]],
  }

}
