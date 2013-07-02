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

class postgresql::initdb(
  $datadir     = $postgresql::params::datadir,
  $encoding    = $postgresql::params::charset,
  $group       = $postgresql::params::group,
  $initdb_path = $postgresql::params::initdb_path,
  $user        = $postgresql::params::user
) inherits postgresql::params {
  # Build up the initdb command.
  #
  # We optionally add the locale switch if specified. Older versions of the
  # initdb command don't accept this switch. So if the user didn't pass the
  # parameter, lets not pass the switch at all.
  $initdb_command = $postgresql::params::locale ? {
    undef   => "${initdb_path} --encoding '${encoding}' --pgdata '${datadir}'",
    default => "${initdb_path} --encoding '${encoding}' --pgdata '${datadir}' --locale '${postgresql::params::locale}'"
  }

  # This runs the initdb command, we use the existance of the PG_VERSION file to
  # ensure we don't keep running this command.
  exec { 'postgresql_initdb':
    command   => $initdb_command,
    creates   => "${datadir}/PG_VERSION",
    user      => $user,
    group     => $group,
    logoutput => on_failure,
  }

  # If we manage the package (which is user configurable) make sure the
  # package exists first.
  if defined(Package[$postgresql::params::server_package_name]) {
    Package[$postgresql::params::server_package_name]->
      Exec['postgresql_initdb']
  }
}
