#
# num2bool.rb
#

# TODO(Krzysztof Wilczynski): We probably need to approach numeric values differently ...

module Puppet::Parser::Functions
  newfunction(:num2bool, :type => :rvalue, :doc => <<-EOS
This function converts a number into a true boolean. Zero becomes false. Numbers
higher then 0 become true.
    EOS
  ) do |arguments|

    raise(Puppet::ParseError, "num2bool(): Wrong number of arguments " +
      "given (#{arguments.size} for 1)") if arguments.size < 1

    number = arguments[0]

    # Only numbers allowed ...
    unless number.match(/^\-?\d+$/)
      raise(Puppet::ParseError, 'num2bool(): Requires integer to work with')
    end

    result = case number
      when /^0$/
        false
      when /^\-?\d+$/
        # Numbers in Puppet are often string-encoded which is troublesome ...
        number = number.to_i
        # We yield true for any positive number and false otherwise ...
        number > 0 ? true : false
      else
        raise(Puppet::ParseError, 'num2bool(): Unknown numeric format given')
    end

    return result
  end
end

# vim: set ts=2 sw=2 et :
