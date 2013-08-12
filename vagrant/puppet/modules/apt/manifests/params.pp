class apt::params {
  $root           = '/etc/apt'
  $provider       = '/usr/bin/apt-get'
  $sources_list_d = "${root}/sources.list.d"
  $apt_conf_d     = "${root}/apt.conf.d"
  $preferences_d  = "${root}/preferences.d"

  case $::lsbdistid {
    'debian': {
      $backports_location = 'http://backports.debian.org/debian-backports'
    }
    'ubuntu': {
      case $::lsbdistcodename {
        'hardy','lucid','maverick','natty','oneiric','precise': {
          $backports_location = 'http://us.archive.ubuntu.com/ubuntu'
        }
        default: {
          $backports_location = 'http://old-releases.ubuntu.com/ubuntu'
        }
      }
    }
  }
}
