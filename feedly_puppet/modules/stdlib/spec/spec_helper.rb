dir = File.expand_path(File.dirname(__FILE__))
$LOAD_PATH.unshift File.join(dir, 'lib')

# Don't want puppet getting the command line arguments for rake or autotest
ARGV.clear

require 'puppet'
require 'facter'
require 'mocha'
gem 'rspec', '>=2.0.0'
require 'rspec/expectations'

require 'puppetlabs_spec_helper/module_spec_helper'
