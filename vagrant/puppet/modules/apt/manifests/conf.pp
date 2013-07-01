define apt::conf (
  $ensure   = present,
  $priority = '50',
  $content
) {

  include apt::params

  $apt_conf_d = $apt::params::apt_conf_d

  file { "${apt_conf_d}/${priority}${name}":
    ensure  => $ensure,
    content => $content,
    owner   => root,
    group   => root,
    mode    => '0644',
  }
}
