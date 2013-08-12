# Sets up the concat system.
#
# $concatdir is where the fragments live and is set on the fact concat_basedir.
# Since puppet should always manage files in $concatdir and they should
# not be deleted ever, /tmp is not an option.
#
# $puppetversion should be either 24 or 25 to enable a 24 compatible
# mode, in 24 mode you might see phantom notifies this is a side effect
# of the method we use to clear the fragments directory.
#
# The regular expression below will try to figure out your puppet version
# but this code will only work in 0.24.8 and newer.
#
# It also copies out the concatfragments.sh file to ${concatdir}/bin
class concat::setup {
  $id = $::id
  $root_group = $id ? {
    root    => 0,
    default => $id
  }

  if $::concat_basedir {
    $concatdir = $::concat_basedir
  } else {
    fail ("\$concat_basedir not defined. Try running again with pluginsync enabled")
  }

  $majorversion = regsubst($::puppetversion, '^[0-9]+[.]([0-9]+)[.][0-9]+$', '\1')
  $fragments_source = $majorversion ? {
    24      => 'puppet:///concat/concatfragments.sh',
    default => 'puppet:///modules/concat/concatfragments.sh'
  }

  file{"${concatdir}/bin/concatfragments.sh":
    owner  => $id,
    group  => $root_group,
    mode   => '0755',
    source => $fragments_source;

  [ $concatdir, "${concatdir}/bin" ]:
    ensure => directory,
    owner  => $id,
    group  => $root_group,
    mode   => '0750';

  ## Old versions of this module used a different path.
  '/usr/local/bin/concatfragments.sh':
    ensure => absent;
  }
}
