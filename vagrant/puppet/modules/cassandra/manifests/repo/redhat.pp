class cassandra::repo::redhat(
    $repo_name,
    $baseurl,
    $gpgkey,
    $gpgcheck,
    $enabled
) {
    yumrepo { $repo_name:
        descr    => 'DataStax Distribution for Cassandra',
        baseurl  => $baseurl,
        gpgkey   => $gpgkey,
        gpgcheck => $gpgcheck,
        enabled  => $enabled,
    }
}
