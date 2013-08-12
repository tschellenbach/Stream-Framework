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

define postgresql::psql(
    $db,
    $unless,
    $command     = $title,
    $refreshonly = false,
    $user        = $postgresql::params::user
) {

  include postgresql::params

  # TODO: FIXME: shellquote does not work, and this regex works for trivial
  # things but not nested escaping.  Need a lexer, preferably a ruby SQL parser
  # to catch errors at catalog time.  Possibly https://github.com/omghax/sql ?

  if ($postgresql::params::version != '8.1') {
    $no_password_option = '--no-password'
  }

  $psql = "${postgresql::params::psql_path} ${no_password_option} --tuples-only --quiet --dbname ${db}"

  $quoted_command = regsubst($command, '"', '\\"', 'G')
  $quoted_unless  = regsubst($unless,  '"', '\\"', 'G')

  $final_cmd = "/bin/echo \"${quoted_command}\" | ${psql} |egrep -v -q '^$'"

  notify { "deprecation warning: ${final_cmd}":
    message => 'postgresql::psql is deprecated ; please use postgresql_psql instead.',
  } ->

  exec { $final_cmd:
    cwd         => '/tmp',
    user        => $user,
    returns     => 1,
    unless      => "/bin/echo \"${quoted_unless}\" | ${psql} | egrep -v -q '^$'",
    refreshonly => $refreshonly,
  }
}

