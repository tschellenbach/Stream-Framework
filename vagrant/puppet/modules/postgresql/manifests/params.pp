# Class: postgresql::params
#
#   The postgresql configuration settings.
#
# Parameters:
#
# Actions:
#
# Requires:
#
# Sample Usage:
#

# TODO: add real docs

# This class allows you to use a newer version of postgres, rather than your
# system's default version.
#
# If you want to do that, note that it is important that you use the '->',
# or a before/require metaparameter to make sure that the `params`
# class is evaluated before any of the other classes in the module.
#
# Also note that this class includes the ability to automatically manage
# the yumrepo resource.  If you'd prefer to manage the repo yourself, simply pass
# 'false' or omit the 'manage_repo' parameter--it defaults to 'false'.  You will
# still need to use the 'params' class to specify the postgres version
# number, though, in order for the other classes to be able to find the
# correct paths to the postgres dirs.

class postgresql::params(
  $version                     = $::postgres_default_version,
  $manage_package_repo         = false,
  $package_source              = undef,
  $locale                      = undef,
  $charset                     = 'UTF8',
  $custom_datadir              = undef,
  $custom_confdir              = undef,
  $custom_bindir               = undef,
  $custom_client_package_name  = undef,
  $custom_server_package_name  = undef,
  $custom_contrib_package_name = undef,
  $custom_devel_package_name   = undef,
  $custom_java_package_name    = undef,
  $custom_service_name         = undef,
  $custom_user                 = undef,
  $custom_group                = undef,
  $run_initdb                  = undef
) {
  $user                         = pick($custom_user, 'postgres')
  $group                        = pick($custom_group, 'postgres')
  $ip_mask_deny_postgres_user   = '0.0.0.0/0'
  $ip_mask_allow_all_users      = '127.0.0.1/32'
  $listen_addresses             = 'localhost'
  $ipv4acls                     = []
  $ipv6acls                     = []
  # TODO: figure out a way to make this not platform-specific
  $manage_redhat_firewall       = false


  if ($manage_package_repo) {
    case $::osfamily {
      'RedHat': {
        $rh_pkg_source = pick($package_source, 'yum.postgresql.org')

        case $rh_pkg_source {
          'yum.postgresql.org': {
            class { 'postgresql::package_source::yum_postgresql_org':
              version => $version
            }
          }

          default: {
            fail("Unsupported package source '${rh_pkg_source}' for ${::osfamily} OS family. Currently the only supported source is 'yum.postgresql.org'")
          }
        }
      }

      'Debian': {
        class { 'postgresql::package_source::apt_postgresql_org': }
      }

      default: {
        fail("Unsupported osfamily: ${::osfamily} operatingsystem: ${::operatingsystem}, module ${module_name} currently only supports osfamily RedHat and Debian")
      }
    }
  }


  # This is a bit hacky, but if the puppet nodes don't have pluginsync enabled,
  # they will fail with a not-so-helpful error message.  Here we are explicitly
  # verifying that the custom fact exists (which implies that pluginsync is
  # enabled and succeeded).  If not, we fail with a hint that tells the user
  # that pluginsync might not be enabled.  Ideally this would be handled directly
  # in puppet.
  if ($::postgres_default_version == undef) {
    fail "No value for postgres_default_version facter fact; it's possible that you don't have pluginsync enabled."
  }

  case $::operatingsystem {
    default: {
      $service_provider = undef
    }
  }

  # Amazon Linux's OS Family is 'Linux', operating system 'Amazon'.
  case $::osfamily {
    'RedHat', 'Linux': {
      $needs_initdb             = pick($run_initdb, true)
      $firewall_supported       = true
      $persist_firewall_command = '/sbin/iptables-save > /etc/sysconfig/iptables'

      if $version == $::postgres_default_version {
        $client_package_name  = pick($custom_client_package_name, 'postgresql')
        $server_package_name  = pick($custom_server_package_name, 'postgresql-server')
        $contrib_package_name = pick($custom_contrib_package_name,'postgresql-contrib')
        $devel_package_name   = pick($custom_devel_package_name, 'postgresql-devel')
        $java_package_name    = pick($custom_java_package_name, 'postgresql-jdbc')
        $service_name = pick($custom_service_name, 'postgresql')
        $bindir       = pick($custom_bindir, '/usr/bin')
        $datadir      = pick($custom_datadir, '/var/lib/pgsql/data')
        $confdir      = pick($custom_confdir, $datadir)
      } else {
        $version_parts        = split($version, '[.]')
        $package_version      = "${version_parts[0]}${version_parts[1]}"
        $client_package_name  = pick($custom_client_package_name, "postgresql${package_version}")
        $server_package_name  = pick($custom_server_package_name, "postgresql${package_version}-server")
        $contrib_package_name = pick($custom_contrib_package_name,"postgresql${package_version}-contrib")
        $devel_package_name   = pick($custom_devel_package_name, "postgresql${package_version}-devel")
        $java_package_name    = pick($custom_java_package_name, "postgresql${package_version}-jdbc")
        $service_name = pick($custom_service_name, "postgresql-${version}")
        $bindir       = pick($custom_bindir, "/usr/pgsql-${version}/bin")
        $datadir      = pick($custom_datadir, "/var/lib/pgsql/${version}/data")
        $confdir      = pick($custom_confdir, $datadir)
      }

      $service_status = undef
      $python_package_name="python-psycopg2"
    }

    'Debian': {
      $needs_initdb             = pick($run_initdb, false)
      $firewall_supported       = false
      # TODO: not exactly sure yet what the right thing to do for Debian/Ubuntu is.
      #$persist_firewall_command = '/sbin/iptables-save > /etc/iptables/rules.v4'


      case $::operatingsystem {
        'Debian': {
          $service_name = pick($custom_service_name, 'postgresql')
        }
        'Ubuntu': {
          # thanks, ubuntu
          if($::lsbmajdistrelease == '10' and !$manage_package_repo) {
            $service_name = pick($custom_service_name, "postgresql-${version}")
          } else {
            $service_name = pick($custom_service_name, 'postgresql')
          }
        }
      }

      $client_package_name  = pick($custom_client_package_name, "postgresql-client-${version}")
      $server_package_name  = pick($custom_server_package_name, "postgresql-${version}")
      $contrib_package_name = pick($custom_contrib_package_name, "postgresql-contrib-${version}")
      $devel_package_name   = pick($custom_devel_package_name, 'libpq-dev')
      $java_package_name    = pick($custom_java_package_name, 'libpostgresql-jdbc-java')
      $bindir               = pick($custom_bindir, "/usr/lib/postgresql/${version}/bin")
      $datadir              = pick($custom_datadir, "/var/lib/postgresql/${version}/main")
      $confdir              = pick($custom_confdir, "/etc/postgresql/${version}/main")
      $service_status       = "/etc/init.d/${service_name} status | /bin/egrep -q 'Running clusters: .+|online'"
      $python_package_name  = "python-psycopg2"
    }

    default: {
      fail("Unsupported osfamily: ${::osfamily} operatingsystem: ${::operatingsystem}, module ${module_name} currently only supports osfamily RedHat and Debian")
    }
  }

  $initdb_path          = "${bindir}/initdb"
  $createdb_path        = "${bindir}/createdb"
  $psql_path            = "${bindir}/psql"
  $pg_hba_conf_path     = "${confdir}/pg_hba.conf"
  $postgresql_conf_path = "${confdir}/postgresql.conf"

}
