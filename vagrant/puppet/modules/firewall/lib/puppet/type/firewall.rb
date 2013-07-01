# See: #10295 for more details.
#
# This is a workaround for bug: #4248 whereby ruby files outside of the normal
# provider/type path do not load until pluginsync has occured on the puppetmaster
#
# In this case I'm trying the relative path first, then falling back to normal
# mechanisms. This should be fixed in future versions of puppet but it looks
# like we'll need to maintain this for some time perhaps.
$LOAD_PATH.unshift(File.join(File.dirname(__FILE__),"..",".."))
require 'puppet/util/firewall'

Puppet::Type.newtype(:firewall) do
  include Puppet::Util::Firewall

  @doc = <<-EOS
    This type provides the capability to manage firewall rules within
    puppet.

    **Autorequires:**

    If Puppet is managing the iptables or ip6tables chains specified in the
    `chain` or `jump` parameters, the firewall resource will autorequire
    those firewallchain resources.

    If Puppet is managing the iptables or iptables-persistent packages, and
    the provider is iptables or ip6tables, the firewall resource will
    autorequire those packages to ensure that any required binaries are
    installed.
  EOS

  feature :rate_limiting, "Rate limiting features."
  feature :snat, "Source NATing"
  feature :dnat, "Destination NATing"
  feature :interface_match, "Interface matching"
  feature :icmp_match, "Matching ICMP types"
  feature :owner, "Matching owners"
  feature :state_match, "Matching stateful firewall states"
  feature :reject_type, "The ability to control reject messages"
  feature :log_level, "The ability to control the log level"
  feature :log_prefix, "The ability to add prefixes to log messages"
  feature :mark, "Set the netfilter mark value associated with the packet"
  feature :tcp_flags, "The ability to match on particular TCP flag settings"
  feature :pkttype, "Match a packet type"
  feature :socket, "Match open sockets"
  feature :isfragment, "Match fragments"

  # provider specific features
  feature :iptables, "The provider provides iptables features."

  ensurable do
    desc <<-EOS
      Manage the state of this rule. The default action is *present*.
    EOS

    newvalue(:present) do
      provider.insert
    end

    newvalue(:absent) do
      provider.delete
    end

    defaultto :present
  end

  newparam(:name) do
    desc <<-EOS
      The canonical name of the rule. This name is also used for ordering
      so make sure you prefix the rule with a number:

          000 this runs first
          999 this runs last

      Depending on the provider, the name of the rule can be stored using
      the comment feature of the underlying firewall subsystem.
    EOS
    isnamevar

    # Keep rule names simple - they must start with a number
    newvalues(/^\d+[[:alpha:][:digit:][:punct:][:space:]]+$/)
  end

  newproperty(:action) do
    desc <<-EOS
      This is the action to perform on a match. Can be one of:

      * accept - the packet is accepted
      * reject - the packet is rejected with a suitable ICMP response
      * drop - the packet is dropped

      If you specify no value it will simply match the rule but perform no
      action unless you provide a provider specific parameter (such as *jump*).
    EOS
    newvalues(:accept, :reject, :drop)
  end

  # Generic matching properties
  newproperty(:source) do
    desc <<-EOS
      The source address. For example:

          source => '192.168.2.0/24'

      The source can also be an IPv6 address if your provider supports it.
    EOS

    munge do |value|
      begin
        @resource.host_to_ip(value)
      rescue Exception => e
        self.fail("host_to_ip failed for #{value}, exception #{e}")
      end
    end
  end

  newproperty(:destination) do
    desc <<-EOS
      The destination address to match. For example:

          destination => '192.168.1.0/24'

      The destination can also be an IPv6 address if your provider supports it.
    EOS

    munge do |value|
      begin
        @resource.host_to_ip(value)
      rescue Exception => e
        self.fail("host_to_ip failed for #{value}, exception #{e}")
      end
    end
  end

  newproperty(:sport, :array_matching => :all) do
    desc <<-EOS
      The source port to match for this filter (if the protocol supports
      ports). Will accept a single element or an array.

      For some firewall providers you can pass a range of ports in the format:

          <start_number>-<ending_number>

      For example:

          1-1024

      This would cover ports 1 to 1024.
    EOS

    munge do |value|
      @resource.string_to_port(value, :proto)
    end

    def is_to_s(value)
      should_to_s(value)
    end

    def should_to_s(value)
      value = [value] unless value.is_a?(Array)
      value.join(',')
    end
  end

  newproperty(:dport, :array_matching => :all) do
    desc <<-EOS
      The destination port to match for this filter (if the protocol supports
      ports). Will accept a single element or an array.

      For some firewall providers you can pass a range of ports in the format:

          <start_number>-<ending_number>

      For example:

          1-1024

      This would cover ports 1 to 1024.
    EOS

    munge do |value|
      @resource.string_to_port(value, :proto)
    end

    def is_to_s(value)
      should_to_s(value)
    end

    def should_to_s(value)
      value = [value] unless value.is_a?(Array)
      value.join(',')
    end
  end

  newproperty(:port, :array_matching => :all) do
    desc <<-EOS
      The destination or source port to match for this filter (if the protocol
      supports ports). Will accept a single element or an array.

      For some firewall providers you can pass a range of ports in the format:

          <start_number>-<ending_number>

      For example:

          1-1024

      This would cover ports 1 to 1024.
    EOS

    munge do |value|
      @resource.string_to_port(value, :proto)
    end

    def is_to_s(value)
      should_to_s(value)
    end

    def should_to_s(value)
      value = [value] unless value.is_a?(Array)
      value.join(',')
    end
  end

  newproperty(:proto) do
    desc <<-EOS
      The specific protocol to match for this rule. By default this is
      *tcp*.
    EOS

    newvalues(:tcp, :udp, :icmp, :"ipv6-icmp", :esp, :ah, :vrrp, :igmp, :ipencap, :ospf, :gre, :all)
    defaultto "tcp"
  end

  # tcp-specific
  newproperty(:tcp_flags, :required_features => :tcp_flags) do
    desc <<-EOS
      Match when the TCP flags are as specified.
      Is a string with a list of comma-separated flag names for the mask,
      then a space, then a comma-separated list of flags that should be set.
      The flags are: SYN ACK FIN RST URG PSH ALL NONE
      Note that you specify them in the order that iptables --list-rules
      would list them to avoid having puppet think you changed the flags.
      Example: FIN,SYN,RST,ACK SYN matches packets with the SYN bit set and the
	       ACK,RST and FIN bits cleared.  Such packets are used to request
               TCP  connection initiation.
    EOS
  end


  # Iptables specific
  newproperty(:chain, :required_features => :iptables) do
    desc <<-EOS
      Name of the chain to use. Can be one of the built-ins:

      * INPUT
      * FORWARD
      * OUTPUT
      * PREROUTING
      * POSTROUTING

      Or you can provide a user-based chain.

      The default value is 'INPUT'.
    EOS

    defaultto "INPUT"
    newvalue(/^[a-zA-Z0-9\-_]+$/)
  end

  newproperty(:table, :required_features => :iptables) do
    desc <<-EOS
      Table to use. Can be one of:

      * nat
      * mangle
      * filter
      * raw
      * rawpost

      By default the setting is 'filter'.
    EOS

    newvalues(:nat, :mangle, :filter, :raw, :rawpost)
    defaultto "filter"
  end

  newproperty(:jump, :required_features => :iptables) do
    desc <<-EOS
      The value for the iptables --jump parameter. Normal values are:

      * QUEUE
      * RETURN
      * DNAT
      * SNAT
      * LOG
      * MASQUERADE
      * REDIRECT
      * MARK

      But any valid chain name is allowed.

      For the values ACCEPT, DROP and REJECT you must use the generic
      'action' parameter. This is to enfore the use of generic parameters where
      possible for maximum cross-platform modelling.

      If you set both 'accept' and 'jump' parameters, you will get an error as
      only one of the options should be set.
    EOS

    validate do |value|
      unless value =~ /^[a-zA-Z0-9\-_]+$/
        raise ArgumentError, <<-EOS
          Jump destination must consist of alphanumeric characters, an
          underscore or a yphen.
        EOS
      end

      if ["accept","reject","drop"].include?(value.downcase)
        raise ArgumentError, <<-EOS
          Jump destination should not be one of ACCEPT, REJECT or DROP. Use
          the action property instead.
        EOS
      end

    end
  end

  # Interface specific matching properties
  newproperty(:iniface, :required_features => :interface_match) do
    desc <<-EOS
      Input interface to filter on.
    EOS
    newvalues(/^[a-zA-Z0-9\-\._\+]+$/)
  end

  newproperty(:outiface, :required_features => :interface_match) do
    desc <<-EOS
      Output interface to filter on.
    EOS
    newvalues(/^[a-zA-Z0-9\-\._\+]+$/)
  end

  # NAT specific properties
  newproperty(:tosource, :required_features => :snat) do
    desc <<-EOS
      When using jump => "SNAT" you can specify the new source address using
      this parameter.
    EOS
  end

  newproperty(:todest, :required_features => :dnat) do
    desc <<-EOS
      When using jump => "DNAT" you can specify the new destination address
      using this paramter.
    EOS
  end

  newproperty(:toports, :required_features => :dnat) do
    desc <<-EOS
      For DNAT this is the port that will replace the destination port.
    EOS
  end

  # Reject ICMP type
  newproperty(:reject, :required_features => :reject_type) do
    desc <<-EOS
      When combined with jump => "REJECT" you can specify a different icmp
      response to be sent back to the packet sender.
    EOS
  end

  # Logging properties
  newproperty(:log_level, :required_features => :log_level) do
    desc <<-EOS
      When combined with jump => "LOG" specifies the system log level to log
      to.
    EOS

    munge do |value|
      if value.kind_of?(String)
        value = @resource.log_level_name_to_number(value)
      else
        value
      end

      if value == nil && value != ""
        self.fail("Unable to determine log level")
      end
      value
    end
  end

  newproperty(:log_prefix, :required_features => :log_prefix) do
    desc <<-EOS
      When combined with jump => "LOG" specifies the log prefix to use when
      logging.
    EOS
  end

  # ICMP matching property
  newproperty(:icmp, :required_features => :icmp_match) do
    desc <<-EOS
      When matching ICMP packets, this is the type of ICMP packet to match.

      A value of "any" is not supported. To achieve this behaviour the
      parameter should simply be omitted or undefined.
    EOS

    validate do |value|
      if value == "any"
        raise ArgumentError,
          "Value 'any' is not valid. This behaviour should be achieved " \
          "by omitting or undefining the ICMP parameter."
      end
    end

    munge do |value|
      if value.kind_of?(String)
        # ICMP codes differ between IPv4 and IPv6.
        case @resource[:provider]
        when :iptables
          protocol = 'inet'
        when :ip6tables
          protocol = 'inet6'
        else
          self.fail("cannot work out protocol family")
        end

        value = @resource.icmp_name_to_number(value, protocol)
      else
        value
      end

      if value == nil && value != ""
        self.fail("cannot work out icmp type")
      end
      value
    end
  end

  newproperty(:state, :array_matching => :all, :required_features =>
    :state_match) do

    desc <<-EOS
      Matches a packet based on its state in the firewall stateful inspection
      table. Values can be:

      * INVALID
      * ESTABLISHED
      * NEW
      * RELATED
    EOS

    newvalues(:INVALID,:ESTABLISHED,:NEW,:RELATED)

    # States should always be sorted. This normalizes the resource states to
    # keep it consistent with the sorted result from iptables-save.
    def should=(values)
      @should = super(values).sort_by {|sym| sym.to_s}
    end

    def is_to_s(value)
      should_to_s(value)
    end

    def should_to_s(value)
      value = [value] unless value.is_a?(Array)
      value.join(',')
    end
  end

  # Rate limiting properties
  newproperty(:limit, :required_features => :rate_limiting) do
    desc <<-EOS
      Rate limiting value for matched packets. The format is:
      rate/[/second/|/minute|/hour|/day].

      Example values are: '50/sec', '40/min', '30/hour', '10/day'."
    EOS
  end

  newproperty(:burst, :required_features => :rate_limiting) do
    desc <<-EOS
      Rate limiting burst value (per second) before limit checks apply.
    EOS
    newvalue(/^\d+$/)
  end

  newproperty(:uid, :required_features => :owner) do
    desc <<-EOS
      UID or Username owner matching rule.  Accepts a string argument
      only, as iptables does not accept multiple uid in a single
      statement.
    EOS
  end

  newproperty(:gid, :required_features => :owner) do
    desc <<-EOS
      GID or Group owner matching rule.  Accepts a string argument
      only, as iptables does not accept multiple gid in a single
      statement.
    EOS
  end

  newproperty(:set_mark, :required_features => :mark) do
    desc <<-EOS
      Set the Netfilter mark value associated with the packet.  Accepts either of:
      mark/mask or mark.  These will be converted to hex if they are not already.
    EOS

    munge do |value|
      int_or_hex = '[a-fA-F0-9x]'
      match = value.to_s.match("(#{int_or_hex}+)(/)?(#{int_or_hex}+)?")
      mark = @resource.to_hex32(match[1])

      # Values that can't be converted to hex.
      # Or contain a trailing slash with no mask.
      if mark.nil? or (mark and match[2] and match[3].nil?)
        raise ArgumentError, "MARK value must be integer or hex between 0 and 0xffffffff"
      end

      # Old iptables does not support a mask. New iptables will expect one.
      iptables_version = Facter.fact('iptables_version').value
      mask_required = (iptables_version and Puppet::Util::Package.versioncmp(iptables_version, '1.4.1') >= 0)

      if mask_required
        if match[3].nil?
          value = "#{mark}/0xffffffff"
        else
          mask = @resource.to_hex32(match[3])
          if mask.nil?
            raise ArgumentError, "MARK mask must be integer or hex between 0 and 0xffffffff"
          end
          value = "#{mark}/#{mask}"
        end
      else
        unless match[3].nil?
          raise ArgumentError, "iptables version #{iptables_version} does not support masks on MARK rules"
        end
        value = mark
      end

      value
    end
  end

  newproperty(:pkttype, :required_features => :pkttype) do
    desc <<-EOS
      Sets the packet type to match.
    EOS

    newvalues(:unicast, :broadcast, :multicast)
  end

  newproperty(:isfragment, :required_features => :isfragment) do
    desc <<-EOS
      Set to true to match tcp fragments (requires type to be set to tcp)
    EOS

    newvalues(:true, :false)
  end

  newproperty(:socket, :required_features => :socket) do
    desc <<-EOS
      If true, matches if an open socket can be found by doing a coket lookup
      on the packet.
    EOS

    newvalues(:true, :false)
  end

  newparam(:line) do
    desc <<-EOS
      Read-only property for caching the rule line.
    EOS
  end

  autorequire(:firewallchain) do
    reqs = []
    protocol = nil

    case value(:provider)
    when :iptables
      protocol = "IPv4"
    when :ip6tables
      protocol = "IPv6"
    end

    unless protocol.nil?
      [value(:chain), value(:jump)].each do |chain|
        reqs << "#{chain}:#{value(:table)}:#{protocol}" unless chain.nil?
      end
    end

    reqs
  end

  # Classes would be a better abstraction, pending:
  # http://projects.puppetlabs.com/issues/19001
  autorequire(:package) do
    case value(:provider)
    when :iptables, :ip6tables
      %w{iptables iptables-persistent}
    else
      []
    end
  end

  validate do
    debug("[validate]")

    # TODO: this is put here to skip validation if ensure is not set. This
    # is because there is a revalidation stage called later where the values
    # are not set correctly. I tried tracing it - but have put in this
    # workaround instead to skip. Must get to the bottom of this.
    if ! value(:ensure)
      return
    end

    # First we make sure the chains and tables are valid combinations
    if value(:table).to_s == "filter" &&
      value(:chain) =~ /PREROUTING|POSTROUTING/

      self.fail "PREROUTING and POSTROUTING cannot be used in table 'filter'"
    end

    if value(:table).to_s == "nat" && value(:chain) =~ /INPUT|FORWARD/
      self.fail "INPUT and FORWARD cannot be used in table 'nat'"
    end

    if value(:table).to_s == "raw" &&
      value(:chain) =~ /INPUT|FORWARD|POSTROUTING/

      self.fail "INPUT, FORWARD and POSTROUTING cannot be used in table raw"
    end

    # Now we analyse the individual properties to make sure they apply to
    # the correct combinations.
    if value(:iniface)
      unless value(:chain).to_s =~ /INPUT|FORWARD|PREROUTING/
        self.fail "Parameter iniface only applies to chains " \
          "INPUT,FORWARD,PREROUTING"
      end
    end

    if value(:outiface)
      unless value(:chain).to_s =~ /OUTPUT|FORWARD|POSTROUTING/
        self.fail "Parameter outiface only applies to chains " \
          "OUTPUT,FORWARD,POSTROUTING"
      end
    end

    if value(:uid)
      unless value(:chain).to_s =~ /OUTPUT|POSTROUTING/
        self.fail "Parameter uid only applies to chains " \
          "OUTPUT,POSTROUTING"
      end
    end

    if value(:gid)
      unless value(:chain).to_s =~ /OUTPUT|POSTROUTING/
        self.fail "Parameter gid only applies to chains " \
          "OUTPUT,POSTROUTING"
      end
    end

    if value(:set_mark)
      unless value(:jump).to_s  =~ /MARK/ &&
             value(:chain).to_s =~ /PREROUTING|OUTPUT/ &&
             value(:table).to_s =~ /mangle/
        self.fail "Parameter set_mark only applies to " \
          "the PREROUTING or OUTPUT chain of the mangle table and when jump => MARK"
      end
    end

    if value(:dport)
      unless value(:proto).to_s =~ /tcp|udp|sctp/
        self.fail "[%s] Parameter dport only applies to sctp, tcp and udp " \
          "protocols. Current protocol is [%s] and dport is [%s]" %
          [value(:name), should(:proto), should(:dport)]
      end
    end

    if value(:jump).to_s == "DNAT"
      unless value(:table).to_s =~ /nat/
        self.fail "Parameter jump => DNAT only applies to table => nat"
      end

      unless value(:todest)
        self.fail "Parameter jump => DNAT must have todest parameter"
      end
    end

    if value(:jump).to_s == "SNAT"
      unless value(:table).to_s =~ /nat/
        self.fail "Parameter jump => SNAT only applies to table => nat"
      end

      unless value(:tosource)
        self.fail "Parameter jump => DNAT must have tosource parameter"
      end
    end

    if value(:jump).to_s == "REDIRECT"
      unless value(:toports)
        self.fail "Parameter jump => REDIRECT missing mandatory toports " \
          "parameter"
      end
    end

    if value(:jump).to_s == "MASQUERADE"
      unless value(:table).to_s =~ /nat/
        self.fail "Parameter jump => MASQUERADE only applies to table => nat"
      end
    end

    if value(:log_prefix) || value(:log_level)
      unless value(:jump).to_s == "LOG"
        self.fail "Parameter log_prefix and log_level require jump => LOG"
      end
    end

    if value(:burst) && ! value(:limit)
      self.fail "burst makes no sense without limit"
    end

    if value(:action) && value(:jump)
      self.fail "Only one of the parameters 'action' and 'jump' can be set"
    end
  end
end
