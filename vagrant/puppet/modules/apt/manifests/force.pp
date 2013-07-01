# force.pp
# force a package from a specific release

define apt::force(
  $release = 'testing',
  $version = false
) {

  $version_string = $version ? {
    false   => undef,
    default => "=${version}",
  }

  $install_check = $version ? {
    false   => "/usr/bin/dpkg -s ${name} | grep -q 'Status: install'",
    default => "/usr/bin/dpkg -s ${name} | grep -q 'Version: ${version}'",
  }
  exec { "/usr/bin/aptitude -y -t ${release} install ${name}${version_string}":
    unless => $install_check,
  }
}
