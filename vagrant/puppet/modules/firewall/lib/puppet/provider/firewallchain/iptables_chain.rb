Puppet::Type.type(:firewallchain).provide :iptables_chain do
  include Puppet::Util::Firewall

  @doc = "Iptables chain provider"

  has_feature :iptables_chain
  has_feature :policy

  optional_commands({
    :iptables       => 'iptables',
    :iptables_save  => 'iptables-save',
    :ip6tables      => 'ip6tables',
    :ip6tables_save => 'ip6tables-save',
    :ebtables       => 'ebtables',
    :ebtables_save  => 'ebtables-save',
  })

  defaultfor :kernel => :linux

  # chain name is greedy so we anchor from the end.
  # [\d+:\d+] doesn't exist on ebtables
  Mapping = {
    :IPv4 => {
      :tables => method(:iptables),
      :save   => method(:iptables_save),
      :re     => /^:(.+)\s(\S+)\s\[\d+:\d+\]$/,
    },
    :IPv6 => {
      :tables => method(:ip6tables),
      :save   => method(:ip6tables_save),
      :re     => /^:(.+)\s(\S+)\s\[\d+:\d+\]$/,
    },
    :ethernet => {
      :tables => method(:ebtables),
      :save   => method(:ebtables_save),
      :re     => /^:(.+)\s(\S+)$/,
    }
  }
  InternalChains = /^(PREROUTING|POSTROUTING|BROUTING|INPUT|FORWARD|OUTPUT)$/
  Tables = 'nat|mangle|filter|raw|rawpost|broute'
  Nameformat = /^(.+):(#{Tables}):(IP(v[46])?|ethernet)$/

  def create
    # can't create internal chains
    if @resource[:name] =~ InternalChains
      self.warn "Attempting to create internal chain #{@resource[:name]}"
    end
    allvalidchains do |t, chain, table, protocol|
      if properties[:ensure] == protocol
        debug "Skipping Inserting chain #{chain} on table #{table} (#{protocol}) already exists"
      else
        debug "Inserting chain #{chain} on table #{table} (#{protocol}) using #{t}"
        t.call ['-t',table,'-N',chain]
        unless @resource[:policy].nil?
          t.call ['-t',table,'-P',chain,@resource[:policy].to_s.upcase]
        end
      end
    end
  end

  def destroy
    # can't delete internal chains
    if @resource[:name] =~ InternalChains
      self.warn "Attempting to destroy internal chain #{@resource[:name]}"
    end
    allvalidchains do |t, chain, table|
      debug "Deleting chain #{chain} on table #{table}"
      t.call ['-t',table,'-X',chain]
    end
  end

  def exists?
    properties[:ensure] == :present
  end

  def policy=(value)
    return if value == :empty
    allvalidchains do |t, chain, table|
      p = ['-t',table,'-P',chain,value.to_s.upcase]
      debug "[set policy] #{t} #{p}"
      t.call p
    end
  end

  def policy
    debug "[get policy] #{@resource[:name]} =#{@property_hash[:policy].to_s.downcase}"
    return @property_hash[:policy].to_s.downcase
  end

  def self.prefetch(resources)
    debug("[prefetch(resources)]")
    instances.each do |prov|
      if resource = resources[prov.name]
        resource.provider = prov
      end
    end
  end

  def flush
    debug("[flush]")
    persist_iptables(@resource[:name].match(Nameformat)[3])
    # Clear the property hash so we re-initialize with updated values
    @property_hash.clear
  end

  # Look up the current status. This allows us to conventiently look up
  # existing status with properties[:foo].
  def properties
    if @property_hash.empty?
      @property_hash = query || {:ensure => :absent}
    end
    @property_hash.dup
  end

  # Pull the current state of the list from the full list.
  def query
    self.class.instances.each do |instance|
      if instance.name == self.name
        debug "query found #{self.name}" % instance.properties.inspect
        return instance.properties
      end
    end
    nil
  end

  def self.instances
    debug "[instances]"
    table = nil
    chains = []

    Mapping.each { |p, c|
      begin
        c[:save].call.each_line do |line|
          if line =~ c[:re] then
            name = $1 + ':' + (table == 'filter' ? 'filter' : table) + ':' + p.to_s
            policy = $2 == '-' ? nil : $2.downcase.to_sym

            chains << new({
              :name   => name,
              :policy => policy,
              :ensure => :present,
            })

            debug "[instance] '#{name}' #{policy}"
          elsif line =~ /^\*(\S+)/
            table = $1
          else
            next
          end
        end
      rescue Puppet::Error
        # ignore command not found for ebtables or anything that doesn't exist
      end
    }

    chains
  end

  def allvalidchains
    @resource[:name].match(Nameformat)
    chain = $1
    table = $2
    protocol = $3
    yield Mapping[protocol.to_sym][:tables],chain,table,protocol.to_sym
  end

end
