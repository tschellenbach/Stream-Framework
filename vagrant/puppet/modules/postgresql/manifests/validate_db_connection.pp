# Define: postgresql::validate_db_connection
#
# This type validates that a successful postgres connection can be established
# between the node on which this resource is run and a specified postgres
# instance (host/port/user/password/database name).
#
# Parameters:
#   [*database_host*]       - the hostname or IP address of the machine where the
#                             postgres server should be running.
#   [*database_port*]       - the port on which postgres server should be
#                             listening (defaults to 5432).
#   [*database_username*]   - the postgres username
#   [*database_password*]   - the postgres user's password
#   [*database_name*]       - the database name that the connection should be
#                             established against
#
# NOTE: to some degree this type assumes that you've created the corresponding
# postgres database instance that you are validating by using the
# `postgresql::db` or `postgresql::database` type provided by this module
# elsewhere in your manifests.
#
# Actions:
#
# Attempts to establish a connection to the specified postgres database.  If
#  a connection cannot be established, the resource will fail; this allows you
#  to use it as a dependency for other resources that would be negatively
#  impacted if they were applied without the postgres connection being available.
#
# Requires:
#
#  `psql` commandline tool (will automatically install the system's postgres
#                           client package if it is not already installed.)
#
# Sample Usage:
#
#  postgresql::validate_db_connection { 'validate my postgres connection':
#      database_host           => 'my.postgres.host',
#      database_username       => 'mydbuser',
#      database_password       => 'mydbpassword',
#      database_name           => 'mydbname',
#  }
#

define postgresql::validate_db_connection(
  $database_host,
  $database_name,
  $database_password,
  $database_username,
  $database_port = 5432
) {
  require postgresql::client

  # TODO: port to ruby
  $psql = "${postgresql::params::psql_path} --tuples-only --quiet -h ${database_host} -U ${database_username} -p ${database_port} --dbname ${database_name}"

  $exec_name = "validate postgres connection for ${database_host}/${database_name}"
  exec { $exec_name:
    command     => '/bin/false',
    unless      => "/bin/echo \"SELECT 1\" | ${psql}",
    cwd         => '/tmp',
    environment => "PGPASSWORD=${database_password}",
    logoutput   => 'on_failure',
    require     => Package['postgresql-client'],
  }

  # This is a little bit of puppet magic.  What we want to do here is make
  # sure that if the validation and the database instance creation are being
  # applied on the same machine, then the database resource is applied *before*
  # the validation resource.  Otherwise, the validation is guaranteed to fail
  # on the first run.
  #
  # We accomplish this by using Puppet's resource collection syntax to search
  # for the Database resource in our current catalog; if it exists, the
  # appropriate relationship is created here.
  Database<|title == $database_name|> -> Exec[$exec_name]
}

