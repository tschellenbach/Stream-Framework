define apt::key (
  $key = $title,
  $ensure = present,
  $key_content = false,
  $key_source = false,
  $key_server = 'keyserver.ubuntu.com'
) {

  include apt::params

  $upkey = upcase($key)

  if $key_content {
    $method = 'content'
  } elsif $key_source {
    $method = 'source'
  } elsif $key_server {
    $method = 'server'
  }

  # This is a hash of the parts of the key definition that we care about.
  # It is used as a unique identifier for this instance of apt::key. It gets
  # hashed to ensure that the resource name doesn't end up being pages and
  # pages (e.g. in the situation where key_content is specified).
  $digest = sha1("${upkey}/${key_content}/${key_source}/${key_server}/")

  # Allow multiple ensure => present for the same key to account for many
  # apt::source resources that all reference the same key.
  case $ensure {
    present: {

      anchor { "apt::key/${title}": }

      if defined(Exec["apt::key ${upkey} absent"]) {
        fail("Cannot ensure Apt::Key[${upkey}] present; ${upkey} already ensured absent")
      }

      if !defined(Anchor["apt::key ${upkey} present"]) {
        anchor { "apt::key ${upkey} present": }
      }

      if !defined(Exec[$digest]) {
        $digest_command = $method ? {
          'content' => "echo '${key_content}' | /usr/bin/apt-key add -",
          'source'  => "wget -q '${key_source}' -O- | apt-key add -",
          'server'  => "apt-key adv --keyserver '${key_server}' --recv-keys '${upkey}'",
        }
        exec { $digest:
          path    => '/bin:/usr/bin',
          unless  => "/usr/bin/apt-key list | /bin/grep '${upkey}'",
          before  => Anchor["apt::key ${upkey} present"],
          command => $digest_command,
        }
      }

      Anchor["apt::key $upkey present"] -> Anchor["apt::key/$title"]

    }
    absent: {

      if defined(Anchor["apt::key ${upkey} present"]) {
        fail("Cannot ensure Apt::Key[${upkey}] absent; ${upkey} already ensured present")
      }

      exec { "apt::key ${upkey} absent":
        path    => '/bin:/usr/bin',
        onlyif  => "apt-key list | grep '${upkey}'",
        command => "apt-key del '${upkey}'",
        user    => 'root',
        group   => 'root',
      }
    }

    default: {
      fail "Invalid 'ensure' value '${ensure}' for aptkey"
    }
  }
}
