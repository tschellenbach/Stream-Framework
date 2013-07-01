# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.customize ["modifyvm", :id, "--memory", 1024]
  config.vm.network :hostonly, '192.168.50.55'
  config.vm.provision :puppet do |puppet|
     puppet.manifests_path = "vagrant/puppet/manifests"
     puppet.module_path = "vagrant/puppet/modules"
     puppet.manifest_file  = "local_dev.pp"
   end
end
