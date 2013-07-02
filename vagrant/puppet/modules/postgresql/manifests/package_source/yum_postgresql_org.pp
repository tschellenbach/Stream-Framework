class postgresql::package_source::yum_postgresql_org(
  $version
) {

  $version_parts       = split($version, '[.]')
  $package_version     = "${version_parts[0]}${version_parts[1]}"

  file { "/etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-${package_version}":
      source => 'puppet:///modules/postgresql/RPM-GPG-KEY-PGDG'
  } ->

  yumrepo { 'yum.postgresql.org':
      descr    => "PostgreSQL ${version} \$releasever - \$basearch",
      baseurl  => "http://yum.postgresql.org/${version}/redhat/rhel-\$releasever-\$basearch",
      enabled  => 1,
      gpgcheck => 1,
      gpgkey   => "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-${package_version}",
  }

  Yumrepo['yum.postgresql.org'] -> Package<|tag == 'postgresql'|>

}
