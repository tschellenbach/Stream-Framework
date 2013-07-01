require 'spec_helper'
describe 'apt::pin', :type => :define do
  let(:title) { 'my_pin' }

  let :default_params do
    {
      :ensure   => 'present',
      :packages => '*',
      :priority => '0',
      :release  => nil
    }
  end

  [ {},
    {
      :packages  => 'apache',
      :priority  => '1'
    },
    {
      :ensure    => 'absent',
      :packages  => 'apache',
      :priority  => '1'
    },
    {
      :packages  => 'apache',
      :priority  => '1',
      :release   => 'my_newpin'
    }
  ].each do |param_set|
    describe "when #{param_set == {} ? "using default" : "specifying"} define parameters" do
      let :param_hash do
        default_params.merge(param_set)
      end

      let :params do
        param_set
      end

      it { should include_class("apt::params") }

      it { should contain_file("#{title}.pref").with({
          'ensure'  => param_hash[:ensure],
          'path'    => "/etc/apt/preferences.d/#{title}.pref",
          'owner'   => 'root',
          'group'   => 'root',
          'mode'    => '0644',
          'content' => "# #{title}\nPackage: #{param_hash[:packages]}\nPin: release a=#{param_hash[:release] || title}\nPin-Priority: #{param_hash[:priority]}\n",
        })
      }
    end
  end
end
