require 'spec_helper'

describe 'cassandra' do

  let(:facts)  do
    { :osfamily => 'Debian',
      :processorcount => 4,
      :lsbdistcodename => 'squeeze',
      :ipaddress => '1.2.3.4'
    }
  end

  let(:params) {{ :seeds => ['1.2.3.4'] }}

  context 'verify module' do

    it 'does contain anchor cassandra::begin ' do
      should contain_anchor('cassandra::begin')
    end

    it 'does contain class cassandra::repo' do
      ## Default params from cassandra::params
      should contain_class('cassandra::repo').with({
        :repo_name => 'datastax',
        :baseurl   => 'http://debian.datastax.com/community',
        :gpgkey    => 'http://debian.datastax.com/debian/repo_key',
        :repos     => 'main',
        :release   => 'stable',
        :pin       => '200',
        :gpgcheck  => 0,
        :enabled   => 1,
      })
    end

    ## Install related resources. No dedicated spec file as it references variables
    ## from cassandra
    it 'does contain class cassandra::install' do
      should contain_class('cassandra::install')
    end

    it 'does contain package dsc' do
      should contain_package('dsc').with({
        :ensure => 'installed',
        :name    => 'dsc12',
      })
    end

    it 'does contain package python-cql' do
      should contain_package('python-cql').with({
        :ensure => 'installed',
      })
    end

    it 'does contain directory /etc/cassandra' do
      should contain_file('CASSANDRA-2356 /etc/cassandra').with({
        :ensure => 'directory',
        :path   => '/etc/cassandra',
        :owner  => 'root',
        :group  => 'root',
        :mode   => '0755',
      })
    end

    it 'does contain file /etc/cassandra/CASSANDRA-2356' do
      should contain_file('CASSANDRA-2356 marker file').with({
        :ensure  => 'file',
        :path    => '/etc/cassandra/CASSANDRA-2356',
        :owner   => 'root',
        :group   => 'root',
        :mode    => '0644',
        :require => ['File[CASSANDRA-2356 /etc/cassandra]', 'Exec[CASSANDRA-2356 Workaround]'],
      })
    end

    it 'does contain exec CASSANDRA-2356 Workaround' do
      should contain_exec('CASSANDRA-2356 Workaround').with({
        :command => '/etc/init.d/cassandra stop && rm -rf /var/lib/cassandra/*',
        :creates => '/etc/cassandra/CASSANDRA-2356',
        :require => ['Package[dsc]', 'File[CASSANDRA-2356 /etc/cassandra]'],
      })
    end
    ## /Finished install resources

    it 'does contain class cassandra::config' do
      should contain_class('cassandra::config').with({
        :max_heap_size              => '',
        :heap_newsize               => '',
        :jmx_port                   => 7199,
        :additional_jvm_opts        => [],
        :cluster_name               => 'Cassandra',
        :listen_address             => '1.2.3.4',
        :rpc_address                => '0.0.0.0',
        :rpc_port                   => 9160,
        :rpc_server_type            => 'hsha',
        :storage_port               => 7000,
        :partitioner                => 'org.apache.cassandra.dht.Murmur3Partitioner',
        :data_file_directories      => ['/var/lib/cassandra/data'],
        :commitlog_directory        => '/var/lib/cassandra/commitlog',
        :saved_caches_directory     => '/var/lib/cassandra/saved_caches',
        :initial_token              => '',
        :seeds                      => ['1.2.3.4'],
        :concurrent_reads           => 32,
        :concurrent_writes          => 32,
        :incremental_backups        => 'false',
        :snapshot_before_compaction => 'false',
        :auto_snapshot              => 'true',
        :multithreaded_compaction   => 'false',
        :endpoint_snitch            => 'SimpleSnitch',
        :internode_compression      => 'all',
        :disk_failure_policy        => 'stop',
        :start_native_transport     => 'false',
        :start_rpc                  => 'true',
        :native_transport_port      => 9042,
        :num_tokens                 => 256,
      })
    end

    ## ervice related resources. No dedicated spec file as it references variables
    ## from cassandra
    it 'does contain class cassandra::service' do
      should contain_class('cassandra::service')
    end

    it 'does contain service cassandra' do
      should contain_service('cassandra').with({
        :ensure     => 'running',
        :enable     => 'true',
        :hasstatus  => 'true',
        :hasrestart => 'true',
        :subscribe  => 'Class[Cassandra::Config]',
        :require    => 'Class[Cassandra::Config]',
      })
    end
    ## /Finished install resources

    it 'does contain anchor cassandra::end ' do
      should contain_anchor('cassandra::end')
    end
  end

  context 'verify parameter' do

    ## Array of arrays: {parameter => [[valid], [invalid]]}
    test_pattern = {
                    :include_repo               => [[true, false], ['bozo']],
                    :commitlog_directory        => [['/tmp/test'], ['test/']],
                    :saved_caches_directory     => [['/tmp/test'], ['test/']],
                    :cluster_name               => [['bozo'], [true]],
                    :partitioner                => [['bozo'], [true]],
                    :initial_token              => [['bozo'], [true]],
                    :endpoint_snitch            => [['bozo'], [true]],
                    :rpc_server_type            => [['hsha', 'sync', 'async'], [9, 'bozo', true]],
                    :incremental_backups        => [['true', 'false'], [9, 'bozo']],
                    :snapshot_before_compaction => [['true', 'false'], [9, 'bozo']],
                    :auto_snapshot              => [['true', 'false'], [9, 'bozo']],
                    :multithreaded_compaction   => [['true', 'false'], [9, 'bozo']],
                    :concurrent_reads           => [[1, 256, 42], ['bozo', 0.5, true]],
                    :concurrent_writes          => [[1, 256, 42], ['bozo', 0.5, true]],
                    :additional_jvm_opts        => [[['a', 'b']], ['bozo']],
                    :seeds                      => [[['a', 'b']], ['bozo', []]],
                    :data_file_directories      => [[['a', 'b']], ['bozo', '']],
                    :jmx_port                   => [[1, 65535], [420000, true]],
                    :listen_address             => [['1.2.3.4'], ['4.5.6']],
                    :rpc_address                => [['1.2.3.4'], ['4.5.6']],
                    :rpc_port                   => [[1, 65535], [420000, true]],
                    :storage_port               => [[1, 65535], [420000, true]],
                    :internode_compression      => [['all', 'dc' ,'none'], [9, 'bozo', true]],
                    :disk_failure_policy        => [['stop', 'best_effort', 'ignore'], [9, 'bozo', true]],
                    :start_native_transport     => [['true', 'false'], [9, 'bozo']],
                    :start_rpc                  => [['true', 'false'], [9, 'bozo']],
                    :native_transport_port      => [[1, 65535], [420000, true]],
                    :num_tokens                 => [[1, 100000], [-1, true, 'bozo']],
    }

    test_pattern.each do |param, pattern|

      describe "#{param} " do
        
        pattern[0].each do |p|

          let(:params) {{ :seeds => ['1.2.3.4'], param => p }}

          it "succeeds with #{p}" do
            should contain_class('cassandra::install')
          end
        end
      end

      describe "#{param}" do

        pattern[1].each do |p|
        
          let(:params) {{ :seeds => ['1.2.3.4'], param => p }}

          it "fails with #{p}" do
            expect {
              should contain_class('cassandra::install')
            }.to raise_error(Puppet::Error)
          end
        end
      end
    end
  end
end
