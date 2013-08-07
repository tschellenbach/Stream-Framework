Puppet::Type.type(:postgresql_psql).provide(:ruby) do

  def command()
    if ((! resource[:unless]) or (resource[:unless].empty?))
      if (resource[:refreshonly])
        # So, if there's no 'unless', and we're in "refreshonly" mode,
        # we need to return the target command here.  If we don't,
        # then Puppet will generate an event indicating that this
        # property has changed.
        return resource[:command]
      end

      # if we're not in refreshonly mode, then we return nil,
      # which will cause Puppet to sync this property.  This
      # is what we want if there is no 'unless' value specified.
      return nil
    end

    output, status = run_unless_sql_command(resource[:unless])

    if status != 0
      self.fail("Error evaluating 'unless' clause: '#{output}'")
    end
    result_count = output.strip.to_i
    if result_count > 0
      # If the 'unless' query returned rows, then we don't want to execute
      # the 'command'.  Returning the target 'command' here will cause
      # Puppet to treat this property as already being 'insync?', so it
      # won't call the setter to run the 'command' later.
      return resource[:command]
    end

    # Returning 'nil' here will cause Puppet to see this property
    # as out-of-sync, so it will call the setter later.
    nil
  end

  def command=(val)
    output, status = run_sql_command(val)

    if status != 0
      self.fail("Error executing SQL; psql returned #{status}: '#{output}'")
    end
  end


  def run_unless_sql_command(sql)
    # for the 'unless' queries, we wrap the user's query in a 'SELECT COUNT',
    # which makes it easier to parse and process the output.
    run_sql_command('SELECT COUNT(*) FROM (' <<  sql << ') count')
  end

  def run_sql_command(sql)
    command = [resource[:psql_path]]
    command.push("-d", resource[:db]) if resource[:db]
    command.push("-t", "-c", sql)

    if resource[:cwd]
      Dir.chdir resource[:cwd] do
        Puppet::Util::SUIDManager.run_and_capture(command, resource[:psql_user], resource[:psql_group])
      end
    else
      Puppet::Util::SUIDManager.run_and_capture(command, resource[:psql_user], resource[:psql_group])
    end
  end

end
