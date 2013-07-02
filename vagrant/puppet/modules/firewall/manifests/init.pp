# Class: firewall
#
# Manages the installation of packages for operating systems that are
# currently supported by the firewall type.
#
class firewall (
  $ensure = running
) {
  case $ensure {
    /^(running|stopped)$/: {
      # Do nothing.
    }
    default: {
      fail("${title}: Ensure value '${ensure}' is not supported")
    }
  }

  case $::kernel {
    'Linux': {
      class { "${title}::linux":
        ensure => $ensure,
      }
    }
    default: {
      fail("${title}: Kernel '${::kernel}' is not currently supported")
    }
  }
}
