#
# delete.rb
#

# TODO(Krzysztof Wilczynski): We need to add support for regular expression ...
# TODO(Krzysztof Wilczynski): Support for strings and hashes too ...

module Puppet::Parser::Functions
  newfunction(:delete, :type => :rvalue, :doc => <<-EOS
Deletes a selected element from an array.

*Examples:*

    delete(['a','b','c'], 'b')

Would return: ['a','c']
    EOS
  ) do |arguments|

    if (arguments.size != 2) then
      raise(Puppet::ParseError, "delete(): Wrong number of arguments "+
        "given #{arguments.size} for 2")
    end

    a = arguments[0]
    item = arguments[1]

    a.delete(item)
    a

  end
end

# vim: set ts=2 sw=2 et :
