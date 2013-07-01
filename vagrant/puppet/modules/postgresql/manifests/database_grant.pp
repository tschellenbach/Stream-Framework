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

# TODO: in mysql module, the grant resource name might look like this: 'user@host/dbname';
#  I think that the API for the resource type should split these up, because it's
#  easier / safer to recombine them for mysql than it is to parse them for other
#  databases.  Also, in the mysql module, the hostname portion of that string
#  affects the user's ability to connect from remote hosts.  In postgres this is
#  managed via pg_hba.conf; not sure if we want to try to reconcile that difference
#  in the modules or not.

define postgresql::database_grant(
  # TODO: mysql supports an array of privileges here.  We should do that if we
  #  port this to ruby.
  $privilege,
  $db,
  $role,
  $psql_db   = $postgresql::params::user,
  $psql_user = $postgresql::params::user
) {
  include postgresql::params

  Postgresql_psql {
    psql_user    => $postgresql::params::user,
    psql_group   => $postgresql::params::group,
    psql_path    => $postgresql::params::psql_path,
  }

  # TODO: FIXME: only works on databases, due to using has_database_privilege

  # TODO: this is a terrible hack; if they pass "ALL" as the desired privilege,
  #  we need a way to test for it--and has_database_privilege does not recognize
  #  'ALL' as a valid privilege name.  So we probably need to hard-code a mapping
  #  between 'ALL' and the list of actual privileges that it entails, and loop
  #  over them to check them.  That sort of thing will probably need to wait until
  #  we port this over to ruby, so, for now, we're just going to assume that if
  #  they have "CREATE" privileges on a database, then they have "ALL".  (I told
  #  you that it was terrible!)
  $unless_privilege = $privilege ? {
    'ALL'   => 'CREATE',
    default => $privilege,
  }

  postgresql_psql {"GRANT ${privilege} ON database \"${db}\" TO \"${role}\"":
    db           => $psql_db,
    psql_user    => $psql_user,
    unless       => "SELECT 1 WHERE has_database_privilege('${role}', '${db}', '${unless_privilege}')",
  }
}
