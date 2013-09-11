# Learn more about module testing here:
# http://docs.puppetlabs.com/guides/tests_smoke.html
class { 'cassandra':
  cluster_name  => 'YourCassandraCluster',
  seeds         => [ '127.0.0.1', ],
}
