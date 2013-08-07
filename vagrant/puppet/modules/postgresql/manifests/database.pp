# puppet-postgresql
# For all details and documentation:
# http://github.com/inkling/puppet-postgresql
#
# Copyright 2012- Inkling Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: in order to match up more closely with the mysql module, this probably
#  needs to be moved over to ruby, and add support for ensurable.

define postgresql::database(
  $dbname   = $title,
  $tablespace = undef,
  $charset  = $postgresql::params::charset,
  $locale   = $postgresql::params::locale
) {
  include postgresql::params

  # Set the defaults for the postgresql_psql resource
  Postgresql_psql {
    psql_user    => $postgresql::params::user,
    psql_group   => $postgresql::params::group,
    psql_path    => $postgresql::params::psql_path,
  }

  # Optionally set the locale switch. Older versions of createdb may not accept
  # --locale, so if the parameter is undefined its safer not to pass it.
  if ($postgresql::params::version != '8.1') {
    $locale_option = $locale ? {
      undef   => '',
      default => "--locale=${locale}",
    }
    $public_revoke_privilege = 'CONNECT'
  } else {
    $locale_option = ''
    $public_revoke_privilege = 'ALL'
  }

  $createdb_command_tmp = "${postgresql::params::createdb_path} --template=template0 --encoding '${charset}' ${locale_option} '${dbname}'"

  if($tablespace == undef) {
    $createdb_command = $createdb_command_tmp
  }
  else {
    $createdb_command = "${createdb_command_tmp} --tablespace='${tablespace}'"
  }

  postgresql_psql { "Check for existence of db '${dbname}'":
    command => 'SELECT 1',
    unless  => "SELECT datname FROM pg_database WHERE datname='${dbname}'",
    require => Class['postgresql::server']
  } ~>

  exec { $createdb_command :
    refreshonly => true,
    user        => $postgresql::params::user,
    logoutput   => on_failure,
  } ~>

  # This will prevent users from connecting to the database unless they've been
  #  granted privileges.
  postgresql_psql {"REVOKE ${public_revoke_privilege} ON DATABASE \"${dbname}\" FROM public":
    db          => $postgresql::params::user,
    refreshonly => true,
  }

}
