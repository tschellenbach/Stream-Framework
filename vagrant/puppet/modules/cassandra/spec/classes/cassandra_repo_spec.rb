require 'spec_helper'

describe 'cassandra::repo' do

  let(:params) do

    { :repo_name => 'rspec_repo', 
      :baseurl   => 'http://cassandra.repo.com/',
      :gpgkey    => 'http://cassandra.repo.com/repo_key',
      :repos     => 'main',
      :release   => 'stable',
      :pin       => 42,
      :gpgcheck  => 0,
      :enabled   => 1,
    }
  end

  context 'on Debian' do

    let(:facts) {{ :osfamily => 'Debian' }}

    it 'does contain class cassandra::repo::debian' do
      should contain_class('cassandra::repo::debian').with({
        :repo_name  => 'rspec_repo',
        :location   => 'http://cassandra.repo.com/',
        :repos      => 'main',
        :release    => 'stable',
        :key_source => 'http://cassandra.repo.com/repo_key',
        :pin        => 42,
      })
    end

    it 'does contain apt::source' do
      should contain_apt__source('rspec_repo').with({
        :location   => 'http://cassandra.repo.com/',
        :repos      => 'main',
        :release    => 'stable',
        :key_source => 'http://cassandra.repo.com/repo_key',
        :pin        => 42,
      })
    end
  end

  context 'on RedHat' do

    let(:facts) {{ :osfamily => 'RedHat' }}

    it 'does contain class cassandra::repo::redhat' do
      should contain_class('cassandra::repo::redhat').with({
        :repo_name => 'rspec_repo',
        :baseurl   => 'http://cassandra.repo.com/',
        :gpgkey    => 'http://cassandra.repo.com/repo_key',
        :gpgcheck  => 0,
        :enabled   => 1,
      })
    end

    it 'does contain yumrepo' do
      should contain_yumrepo('rspec_repo').with({
        :baseurl  => 'http://cassandra.repo.com/',
        :gpgkey   => 'http://cassandra.repo.com/repo_key',
        :gpgcheck => 0,
        :enabled  => 1,
      })
    end
  end

  context 'on some other OS' do

    let(:facts) {{ :osfamily => 'Gentoo' }}

    it 'fails' do
      expect {
        should contain_class('cassandra::repo::gentoo')
      }.to raise_error(Puppet::Error)
    end
  end
end
