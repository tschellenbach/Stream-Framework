# A system to construct files using fragments from other files or templates.
#
# This requires at least puppet 0.25 to work correctly as we use some
# enhancements in recursive directory management and regular expressions
# to do the work here.
#
# USAGE:
# The basic use case is as below:
#
# concat{"/etc/named.conf":
#    notify => Service["named"]
# }
#
# concat::fragment{"foo.com_config":
#    target  => "/etc/named.conf",
#    order   => 10,
#    content => template("named_conf_zone.erb")
# }
#
# # add a fragment not managed by puppet so local users
# # can add content to managed file
# concat::fragment{"foo.com_user_config":
#    target  => "/etc/named.conf",
#    order   => 12,
#    ensure  => "/etc/named.conf.local"
# }
#
# This will use the template named_conf_zone.erb to build a single
# bit of config up and put it into the fragments dir.  The file
# will have an number prefix of 10, you can use the order option
# to control that and thus control the order the final file gets built in.
#
# You can also specify a path and use a different name for your resources:
#
# # You can make this something dynamic, based on whatever parameters your
# # module/class for example.
# $vhost_file = '/etc/httpd/vhosts/01-my-vhost.conf'
#
# concat{'apache-vhost-myvhost':
#   path => $vhost_file,
# }
#
# # We don't care where the file is located, just what to put in it.
# concat::fragment {'apache-vhost-myvhost-main':
#   target  => 'apache-vhost-myvhost',
#   content => '<virtualhost *:80>',
#   order   => 01,
# }
#
# concat::fragment {'apache-vhost-myvhost-close':
#   target  => 'apache-vhost-myvhost',
#   content => '</virtualhost>',
#   order   => 99,
# }
#
#
# SETUP:
# The class concat::setup uses the fact concat_basedir to define the variable
# $concatdir, where all the temporary files and fragments will be
# durably stored. The fact concat_basedir will be set up on the client to
# <Puppet[:vardir]>/concat, so you will be able to run different setup/flavours
# of puppet clients.
# However, since this requires the file lib/facter/concat_basedir.rb to be
# deployed on the clients, so you will have to set "pluginsync = true" on
# both the master and client, at least for the first run.
#
# There's some regular expression magic to figure out the puppet version but
# if you're on an older 0.24 version just set $puppetversion = 24
#
# DETAIL:
# We use a helper shell script called concatfragments.sh that gets placed
# in <Puppet[:vardir]>/concat/bin to do the concatenation.  While this might
# seem more complex than some of the one-liner alternatives you might find on
# the net we do a lot of error checking and safety checks in the script to avoid
# problems that might be caused by complex escaping errors etc.
#
# LICENSE:
# Apache Version 2
#
# LATEST:
# http://github.com/ripienaar/puppet-concat/
#
# CONTACT:
# R.I.Pienaar <rip@devco.net>
# Volcane on freenode
# @ripienaar on twitter
# www.devco.net


# Sets up so that you can use fragments to build a final config file,
#
# OPTIONS:
#  - path       The path to the final file. Use this in case you want to
#               differentiate between the name of a resource and the file path.
#               Note: Use the name you provided in the target of your
#               fragments.
#  - mode       The mode of the final file
#  - owner      Who will own the file
#  - group      Who will own the file
#  - force      Enables creating empty files if no fragments are present
#  - warn       Adds a normal shell style comment top of the file indicating
#               that it is built by puppet
#  - backup     Controls the filebucketing behavior of the final file and
#               see File type reference for its use.  Defaults to 'puppet'
#
# ACTIONS:
#  - Creates fragment directories if it didn't exist already
#  - Executes the concatfragments.sh script to build the final file, this
#    script will create directory/fragments.concat.   Execution happens only
#    when:
#    * The directory changes
#    * fragments.concat != final destination, this means rebuilds will happen
#      whenever someone changes or deletes the final file.  Checking is done
#      using /usr/bin/cmp.
#    * The Exec gets notified by something else - like the concat::fragment
#      define
#  - Copies the file over to the final destination using a file resource
#
# ALIASES:
#  - The exec can notified using Exec["concat_/path/to/file"] or
#    Exec["concat_/path/to/directory"]
#  - The final file can be referened as File["/path/to/file"] or
#    File["concat_/path/to/file"]
define concat(
  $path = $name,
  $owner = $::id,
  $group = $concat::setup::root_group,
  $mode = '0644',
  $warn = false,
  $force = false,
  $backup = 'puppet',
  $gnu = undef,
  $order='alpha'
) {
  include concat::setup

  $safe_name   = regsubst($name, '/', '_', 'G')
  $concatdir   = $concat::setup::concatdir
  $version     = $concat::setup::majorversion
  $fragdir     = "${concatdir}/${safe_name}"
  $concat_name = 'fragments.concat.out'
  $default_warn_message = '# This file is managed by Puppet. DO NOT EDIT.'

  case $warn {
    'true', true, yes, on: {
      $warnmsg = $default_warn_message
    }
    'false', false, no, off: {
      $warnmsg = ''
    }
    default: {
      $warnmsg = $warn
    }
  }

  $warnmsg_escaped = regsubst($warnmsg, "'", "'\\\\''", 'G')
  $warnflag = $warnmsg_escaped ? {
    ''      => '',
    default => "-w '${warnmsg_escaped}'"
  }

  case $force {
    'true', true, yes, on: {
      $forceflag = '-f'
    }
    'false', false, no, off: {
      $forceflag = ''
    }
    default: {
      fail("Improper 'force' value given to concat: ${force}")
    }
  }

  case $order {
    numeric: {
      $orderflag = '-n'
    }
    alpha: {
      $orderflag = ''
    }
    default: {
      fail("Improper 'order' value given to concat: ${order}")
    }
  }

  File {
    owner  => $::id,
    group  => $group,
    mode   => $mode,
    backup => $backup
  }

  file { $fragdir:
    ensure => directory,
  }

  $source_real = $version ? {
    24      => 'puppet:///concat/null',
    default => undef,
  }

  file { "${fragdir}/fragments":
    ensure   => directory,
    force    => true,
    ignore   => ['.svn', '.git', '.gitignore'],
    notify   => Exec["concat_${name}"],
    purge    => true,
    recurse  => true,
    source   => $source_real,
  }

  file { "${fragdir}/fragments.concat":
    ensure   => present,
  }

  file { "${fragdir}/${concat_name}":
    ensure   => present,
  }

  file { $name:
    ensure   => present,
    path     => $path,
    alias    => "concat_${name}",
    group    => $group,
    mode     => $mode,
    owner    => $owner,
    source   => "${fragdir}/${concat_name}",
  }

  exec { "concat_${name}":
    alias       => "concat_${fragdir}",
    command     => "${concat::setup::concatdir}/bin/concatfragments.sh -o ${fragdir}/${concat_name} -d ${fragdir} ${warnflag} ${forceflag} ${orderflag}",
    notify      => File[$name],
    require     => [
      File[$fragdir],
      File["${fragdir}/fragments"],
      File["${fragdir}/fragments.concat"],
    ],
    subscribe   => File[$fragdir],
    unless      => "${concat::setup::concatdir}/bin/concatfragments.sh -o ${fragdir}/${concat_name} -d ${fragdir} -t ${warnflag} ${forceflag} ${orderflag}",
  }

  if $::id == 'root' {
    Exec["concat_${name}"] {
      user  => root,
      group => $group,
    }
  }
}

# vim:sw=2:ts=2:expandtab:textwidth=79
