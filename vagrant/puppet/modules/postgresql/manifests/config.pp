# Class: postgresql::config
#
# Parameters:
#
#   [*postgres_password*]            - postgres db user password.
#   [*ip_mask_deny_postgres_user*]   - ip mask for denying remote access for postgres user; defaults to '0.0.0.0/0',
#                                       meaning that all TCP access for postgres user is denied.
#   [*ip_mask_allow_all_users*]      - ip mask for allowing remote access for other users (besides postgres);
#                                       defaults to '127.0.0.1/32', meaning only allow connections from localhost
#   [*listen_addresses*]             - what IP address(es) to listen on; comma-separated list of addresses; defaults to
#                                       'localhost', '*' = all
#   [*ipv4acls*]                     - list of strings for access control for connection method, users, databases, IPv4
#                                       addresses; see postgresql documentation about pg_hba.conf for information
#   [*ipv6acls*]                     - list of strings for access control for connection method, users, databases, IPv6
#                                       addresses; see postgresql documentation about pg_hba.conf for information
#   [*pg_hba_conf_path*]             - path to pg_hba.conf file
#   [*postgresql_conf_path*]         - path to postgresql.conf file
#   [*manage_redhat_firewall*]       - boolean indicating whether or not the module should open a port in the firewall on
#                                       redhat-based systems; this parameter is likely to change in future versions.  Possible
#                                       changes include support for non-RedHat systems and finer-grained control over the
#                                       firewall rule (currently, it simply opens up the postgres port to all TCP connections).
#
#
# Actions:
#
# Requires:
#
# Usage:
#
#   class { 'postgresql::config':
#     postgres_password         => 'postgres',
#     ip_mask_allow_all_users   => '0.0.0.0/0',
#   }
#
class postgresql::config(
  $postgres_password            = undef,
  $ip_mask_deny_postgres_user   = $postgresql::params::ip_mask_deny_postgres_user,
  $ip_mask_allow_all_users      = $postgresql::params::ip_mask_allow_all_users,
  $listen_addresses             = $postgresql::params::listen_addresses,
  $ipv4acls                     = $postgresql::params::ipv4acls,
  $ipv6acls                     = $postgresql::params::ipv6acls,
  $pg_hba_conf_path             = $postgresql::params::pg_hba_conf_path,
  $postgresql_conf_path         = $postgresql::params::postgresql_conf_path,
  $manage_redhat_firewall       = $postgresql::params::manage_redhat_firewall
) inherits postgresql::params {

  # Basically, all this class needs to handle is passing parameters on
  #  to the "beforeservice" and "afterservice" classes, and ensure
  #  the proper ordering.

  class { 'postgresql::config::beforeservice':
    ip_mask_deny_postgres_user    => $ip_mask_deny_postgres_user,
    ip_mask_allow_all_users       => $ip_mask_allow_all_users,
    listen_addresses              => $listen_addresses,
    ipv4acls                      => $ipv4acls,
    ipv6acls                      => $ipv6acls,
    pg_hba_conf_path              => $pg_hba_conf_path,
    postgresql_conf_path          => $postgresql_conf_path,
    manage_redhat_firewall        => $manage_redhat_firewall,
  }

  class { 'postgresql::config::afterservice':
    postgres_password        => $postgres_password,
  }

  Class['postgresql::config'] ->
      Class['postgresql::config::beforeservice'] ->
      Service['postgresqld'] ->
      Class['postgresql::config::afterservice']


}
