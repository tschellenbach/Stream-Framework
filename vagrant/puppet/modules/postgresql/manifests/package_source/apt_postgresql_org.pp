class postgresql::package_source::apt_postgresql_org {
  # Here we have tried to replicate the instructions on the PostgreSQL site:
  #
  # http://www.postgresql.org/download/linux/debian/
  #
  apt::pin { 'apt.postgresql.org':
    originator => 'apt.postgresql.org',
    priority   => 500,
  }->
  apt::source { 'apt.postgresql.org':
    location          => 'http://apt.postgresql.org/pub/repos/apt/',
    release           => "${::lsbdistcodename}-pgdg",
    repos             => 'main',
    required_packages => 'pgdg-keyring',
    key               => 'ACCC4CF8',
    key_source        => 'http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc',
    include_src       => false,
  }

  Apt::Source['apt.postgresql.org']->Package<|tag == 'postgresql'|>
}
