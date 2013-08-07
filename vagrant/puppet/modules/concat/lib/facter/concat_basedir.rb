Facter.add("concat_basedir") do
    setcode do
        File.join(Puppet[:vardir],"concat")
    end
end
