require 'spec_helper'

describe 'concat' do
  basedir = '/var/lib/puppet/concat'
  let(:title) { '/etc/foo.bar' }
  let(:facts) { {
    :concat_basedir => '/var/lib/puppet/concat',
    :id             => 'root',
  } }
  let :pre_condition do
    'include concat::setup'
  end

  directories = [
    "#{basedir}/_etc_foo.bar",
    "#{basedir}/_etc_foo.bar/fragments",
  ]

  directories.each do |dirs|
    it do
      should contain_file(dirs).with({
        'ensure'  => 'directory',
        'backup'  => 'puppet',
        'group'   => 0,
        'mode'    => '0644',
        'owner'   => 'root',
      })
    end
  end

  files = [
    "/etc/foo.bar",
    "#{basedir}/_etc_foo.bar/fragments.concat",
  ]

  files.each do |file|
    it do
      should contain_file(file).with({
        'ensure'  => 'present',
        'backup'  => 'puppet',
        'group'   => 0,
        'mode'    => '0644',
        'owner'   => 'root',
      })
    end
  end

  it do
    should contain_exec("concat_/etc/foo.bar").with_command(
      "#{basedir}/bin/concatfragments.sh " +
      "-o #{basedir}/_etc_foo.bar/fragments.concat.out " +
      "-d #{basedir}/_etc_foo.bar   "
    )
  end
end

describe 'concat' do

  basedir = '/var/lib/puppet/concat'
  let(:title) { 'foobar' }
  let(:target) { '/etc/foo.bar' }
  let(:facts) { {
    :concat_basedir => '/var/lib/puppet/concat',
    :id             => 'root',
  } }
  let :pre_condition do
    'include concat::setup'
  end

  directories = [
    "#{basedir}/foobar",
    "#{basedir}/foobar/fragments",
  ]

  directories.each do |dirs|
    it do
      should contain_file(dirs).with({
        'ensure'  => 'directory',
        'backup'  => 'puppet',
        'group'   => 0,
        'mode'    => '0644',
        'owner'   => 'root',
      })
    end
  end

  files = [
    "foobar",
    "#{basedir}/foobar/fragments.concat",
  ]

  files.each do |file|
    it do
      should contain_file(file).with({
        'ensure'  => 'present',
        'backup'  => 'puppet',
        'group'   => 0,
        'mode'    => '0644',
        'owner'   => 'root',
      })
    end
  end

  it do
    should contain_exec("concat_foobar").with_command(
      "#{basedir}/bin/concatfragments.sh " +
      "-o #{basedir}/foobar/fragments.concat.out " +
      "-d #{basedir}/foobar   "
    )
  end


end

# vim:sw=2:ts=2:expandtab:textwidth=79
