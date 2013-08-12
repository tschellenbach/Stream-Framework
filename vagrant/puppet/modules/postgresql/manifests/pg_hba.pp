# This resource manages a pg_hba file, collecting fragments of pg_hba_rules
# to build up the final file.
define postgresql::pg_hba(
  $target = $postgresql::params::pg_hba_conf_path,
  $owner = 0,
  $group = $postgresql::params::group
) {
  include postgresql::params
  include concat::setup

  # Collect file from fragments
  concat { $target:
    owner => $owner,
    group => $group,
    mode  => '0640',
    warn  => true,
  }

}
