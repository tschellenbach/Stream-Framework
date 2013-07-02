# Class: postgresql::config::beforeservice
#
# Parameters:
#
#   [*ip_mask_deny_postgres_user*]   - ip mask for denying remote access for postgres user; defaults to '0.0.0.0/0',
#                                       meaning that all TCP access for postgres user is denied.
#   [*ip_mask_allow_all_users*]      - ip mask for allowing remote access for other users (besides postgres);
#                                       defaults to '127.0.0.1/32', meaning only allow connections from localhost
#   [*listen_addresses*]        - what IP address(es) to listen on; comma-separated list of addresses; defaults to
#                                    'localhost', '*' = all
#   [*ipv4acls*]                - list of strings for access control for connection method, users, databases, IPv4
#                                    addresses; see postgresql documentation about pg_hba.conf for information
#   [*ipv6acls*]                - list of strings for access control for connection method, users, databases, IPv6
#                                    addresses; see postgresql documentation about pg_hba.conf for information
#   [*pg_hba_conf_path*]        - path to pg_hba.conf file
#   [*postgresql_conf_path*]    - path to postgresql.conf file
#   [*manage_redhat_firewall*]  - boolean indicating whether or not the module should open a port in the firewall on
#                                    redhat-based systems; this parameter is likely to change in future versions.  Possible
#                                    changes include support for non-RedHat systems and finer-grained control over the
#                                    firewall rule (currently, it simply opens up the postgres port to all TCP connections).
#
# Actions:
#
# Requires:
#
# Usage:
#   This class is not intended to be used directly; it is
#   managed by postgresl::config.  It contains resources
#   that should be handled *before* the postgres service
#   has been started up.
#
#   class { 'postgresql::config::before_service':
#     ip_mask_allow_all_users    => '0.0.0.0/0',
#   }
#
class postgresql::config::beforeservice(
  $pg_hba_conf_path,
  $postgresql_conf_path,
  $ip_mask_deny_postgres_user   = $postgresql::params::ip_mask_deny_postgres_user,
  $ip_mask_allow_all_users      = $postgresql::params::ip_mask_allow_all_users,
  $listen_addresses             = $postgresql::params::listen_addresses,
  $ipv4acls                     = $postgresql::params::ipv4acls,
  $ipv6acls                     = $postgresql::params::ipv6acls,
  $manage_redhat_firewall       = $postgresql::params::manage_redhat_firewall
) inherits postgresql::params {


  File {
    owner  => $postgresql::params::user,
    group  => $postgresql::params::group,
  }

  # Create the main pg_hba resource
  postgresql::pg_hba { 'main':
    notify => Exec['reload_postgresql'],
  }

  Postgresql::Pg_hba_rule {
    database => 'all',
    user => 'all',
  }

  # Lets setup the base rules
  postgresql::pg_hba_rule { 'local access as postgres user':
    type        => 'local',
    user        => 'postgres',
    auth_method => 'ident',
    auth_option => $postgresql::params::version ? {
      '8.1'   => 'sameuser',
      default => undef,
    },
    order       => '001',
  }
  postgresql::pg_hba_rule { 'local access to database with same name':
    type        => 'local',
    auth_method => 'ident',
    auth_option => $postgresql::params::version ? {
      '8.1'   => 'sameuser',
      default => undef,
    },
    order       => '002',
  }
  postgresql::pg_hba_rule { 'deny access to postgresql user':
    type        => 'host',
    user        => 'postgres',
    address     => $ip_mask_deny_postgres_user,
    auth_method => 'reject',
    order       => '003',
  }

  # ipv4acls are passed as an array of rule strings, here we transform them into
  # a resources hash, and pass the result to create_resources
  $ipv4acl_resources = postgresql_acls_to_resources_hash($ipv4acls, 'ipv4acls', 10)
  create_resources('postgresql::pg_hba_rule', $ipv4acl_resources)

  postgresql::pg_hba_rule { 'allow access to all users':
    type        => 'host',
    address     => $ip_mask_allow_all_users,
    auth_method => 'md5',
    order       => '100',
  }
  postgresql::pg_hba_rule { 'allow access to ipv6 localhost':
    type        => 'host',
    address     => '::1/128',
    auth_method => 'md5',
    order       => '101',
  }

  # ipv6acls are passed as an array of rule strings, here we transform them into
  # a resources hash, and pass the result to create_resources
  $ipv6acl_resources = postgresql_acls_to_resources_hash($ipv6acls, 'ipv6acls', 102)
  create_resources('postgresql::pg_hba_rule', $ipv6acl_resources)

  # We must set a "listen_addresses" line in the postgresql.conf if we
  #  want to allow any connections from remote hosts.
  file_line { 'postgresql.conf#listen_addresses':
    path        => $postgresql_conf_path,
    match       => '^listen_addresses\s*=.*$',
    line        => "listen_addresses = '${listen_addresses}'",
    notify      => Service['postgresqld'],
  }

  # Here we are adding an 'include' line so that users have the option of
  # managing their own settings in a second conf file. This only works for
  # postgresql 8.2 and higher.
  if(versioncmp($postgresql::params::version, '8.2') >= 0) {
    # Since we're adding an "include" for this extras config file, we need
    # to make sure it exists.
    exec { "create_postgresql_conf_path":
      command => "touch `dirname ${postgresql_conf_path}`/postgresql_puppet_extras.conf",
      path    => '/usr/bin:/bin',
      unless  => "[ -f `dirname ${postgresql_conf_path}`/postgresql_puppet_extras.conf ]"
    }

    file_line { 'postgresql.conf#include':
      path        => $postgresql_conf_path,
      line        => "include 'postgresql_puppet_extras.conf'",
      require     => Exec["create_postgresql_conf_path"],
      notify      => Service['postgresqld'],
    }
  }


  # TODO: is this a reasonable place for this firewall stuff?
  # TODO: figure out a way to make this not platform-specific; debian and ubuntu have
  #        an out-of-the-box firewall configuration that seems trickier to manage
  # TODO: get rid of hard-coded port
  if ($manage_redhat_firewall and $firewall_supported) {
      exec { 'postgresql-persist-firewall':
        command     => $persist_firewall_command,
        refreshonly => true,
      }

      Firewall {
        notify => Exec['postgresql-persist-firewall']
      }

      firewall { '5432 accept - postgres':
        port   => '5432',
        proto  => 'tcp',
        action => 'accept',
      }
  }
}
