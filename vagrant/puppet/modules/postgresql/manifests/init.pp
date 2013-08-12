# == Class: postgresql
#
# This is a base class that can be used to modify catalog-wide settings relating
# to the various types in class contained in the postgresql module.
#
# If you don't declare this class in your catalog, sensible defaults will
# be used.  However, if you choose to declare it, it needs to appear *before*
# any other types or classes from the postgresql module.
#
# For examples, see the files in the `tests` directory; in particular,
# `/server-yum-postgresql-org.pp`.
#
# === Parameters
#
# [*version*]
#    The postgresql version to install.  If not specified, the
#    module will use whatever version is the default for your
#    OS distro.
# [*manage_package_repo*]
#    This determines whether or not the module should
#    attempt to manage the postgres package repository for your
#    distro.  Defaults to `false`, but if set to `true`, it can
#    be used to set up the official postgres yum/apt package
#    repositories for you.
# [*package_source*]
#    This setting is only used if `manage_package_repo` is
#    set to `true`.  It determines which package repository should
#    be used to install the postgres packages.  Currently supported
#    values include `yum.postgresql.org`.
# [*locale*]
#    This setting defines the default locale for initdb and createdb
#    commands. This default to 'undef' which is effectively 'C'.
# [*charset*]
#    Sets the default charset to be used for initdb and createdb.
#    Defaults to 'UTF8'.
# [*datadir*]
#    This setting can be used to override the default postgresql
#    data directory for the target platform. If not specified, the
#    module will use whatever directory is the default for your
#    OS distro.
# [*confdir*]
#    This setting can be used to override the default postgresql
#    configuration directory for the target platform. If not
#    specified, the module will use whatever directory is the
#    default for your OS distro.
# [*bindir*]
#    This setting can be used to override the default postgresql
#    binaries directory for the target platform. If not
#    specified, the module will use whatever directory is the
#    default for your OS distro.
# [*client_package_name*]
#    This setting can be used to override the default
#    postgresql client package name. If not specified, the module
#    will use whatever package name is the default for your
#    OS distro.
# [*server_package_name*]
#    This setting can be used to override the default
#    postgresql server package name. If not specified, the module
#    will use whatever package name is the default for your
#    OS distro.
# [*contrib_package_name*]
#    This setting can be used to override the default
#    postgresql contrib package name. If not specified, the module
#    will use whatever package name is the default for your
#    OS distro.
# [*devel_package_name*]
#    This setting can be used to override the default
#    postgresql devel package name. If not specified, the module
#    will use whatever package name is the default for your
#    OS distro.
# [*java_package_name*]
#    This setting can be used to override the default
#    postgresql java package name. If not specified, the module
#    will use whatever package name is the default for your
#    OS distro.
# [*service_name*]
#    This setting can be used to override the default
#    postgresql service name. If not specified, the module
#    will use whatever service name is the default for your
#    OS distro.
# [*user*]
#    This setting can be used to override the default
#    postgresql super user and owner of postgresql related files
#    in the file system. If not specified, the module will use
#    the user name 'postgres'.
# [*group*]
#    This setting can be used to override the default
#    postgresql user group to be used for related files
#    in the file system. If not specified, the module will use
#    the group name 'postgres'.
# [*run_initdb*]
#    This setting can be used to explicitly call the initdb
#    operation after server package is installed and before
#    the postgresql service is started. If not specified, the
#    module will decide whether to call initdb or not depending
#    on your OS distro.
#
# === Examples
#
#   class { 'postgresql':
#     version               => '9.2',
#     manage_package_repo   => true,
#   }
#
#
class postgresql (
  $version              = $::postgres_default_version,
  $manage_package_repo  = false,
  $package_source       = undef,
  $locale               = undef,
  $charset              = 'UTF8',
  $datadir              = undef,
  $confdir              = undef,
  $bindir               = undef,
  $client_package_name  = undef,
  $server_package_name  = undef,
  $contrib_package_name = undef,
  $devel_package_name   = undef,
  $java_package_name    = undef,
  $service_name         = undef,
  $user                 = undef,
  $group                = undef,
  $run_initdb           = undef
) {

  class { 'postgresql::params':
    version                     => $version,
    manage_package_repo         => $manage_package_repo,
    package_source              => $package_source,
    locale                      => $locale,
    charset                     => $charset,
    custom_datadir              => $datadir,
    custom_confdir              => $confdir,
    custom_bindir               => $bindir,
    custom_client_package_name  => $client_package_name,
    custom_server_package_name  => $server_package_name,
    custom_contrib_package_name => $contrib_package_name,
    custom_devel_package_name   => $devel_package_name,
    custom_java_package_name    => $java_package_name,
    custom_service_name         => $service_name,
    custom_user                 => $user,
    custom_group                => $group,
    run_initdb                  => $run_initdb,
  }
}
