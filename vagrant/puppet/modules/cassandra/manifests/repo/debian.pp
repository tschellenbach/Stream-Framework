class cassandra::repo::debian(
    $repo_name,
    $location,
    $repos,
    $release,
    $key_source,
    $pin
) {
    apt::source { $repo_name:
        location          => $location,
        release           => $release,
        repos             => $repos,
        key               => $repo_name,
        key_source        => $key_source,
        pin               => $pin,
        include_src       => false,
    }
}
