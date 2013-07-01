#! /usr/bin/env ruby -S rspec
require 'spec_helper'

describe "the num2bool function" do
  let(:scope) { PuppetlabsSpec::PuppetInternals.scope }

  it "should exist" do
    Puppet::Parser::Functions.function("num2bool").should == "function_num2bool"
  end

  it "should raise a ParseError if there is less than 1 arguments" do
    lambda { scope.function_num2bool([]) }.should( raise_error(Puppet::ParseError))
  end

  it "should return true if 1" do
    result = scope.function_num2bool(["1"])
    result.should(be_true)
  end

  it "should return false if 0" do
    result = scope.function_num2bool(["0"])
    result.should(be_false)
  end
end
