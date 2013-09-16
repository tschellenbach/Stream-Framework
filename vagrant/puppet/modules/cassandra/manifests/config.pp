class cassandra::config(
    $config_path,
    $max_heap_size,
    $heap_newsize,
    $jmx_port,
    $additional_jvm_opts,
    $cluster_name,
    $start_native_transport,
    $start_rpc,
    $listen_address,
    $broadcast_address,
    $rpc_address,
    $rpc_port,
    $rpc_server_type,
    $native_transport_port,
    $storage_port,
    $partitioner,
    $data_file_directories,
    $commitlog_directory,
    $saved_caches_directory,
    $initial_token,
    $num_tokens,
    $seeds,
    $concurrent_reads,
    $concurrent_writes,
    $incremental_backups,
    $snapshot_before_compaction,
    $auto_snapshot,
    $multithreaded_compaction,
    $endpoint_snitch,
    $internode_compression,
    $disk_failure_policy,
    $thread_stack_size,
) {
    group { 'cassandra':
        ensure  => present,
        require => Class['cassandra::install'],
    }

    user { 'cassandra':
        ensure  => present,
        require => Group['cassandra'],
    }

    File {
        owner   => 'cassandra',
        group   => 'cassandra',
        mode    => '0644',
        require => Class['cassandra::install'],
    }

    file { $data_file_directories:
        ensure  => directory,
    }

    file { "${config_path}/cassandra-env.sh":
        ensure  => file,
        content => template("${module_name}/cassandra-env.sh.erb"),
    }

    file { "${config_path}/cassandra.yaml":
        ensure  => file,
        content => template("${module_name}/cassandra.yaml.erb"),
    }
}
