What is it?
===========

A Puppet module that can construct files from fragments.

Please see the comments in the various .pp files for details
as well as posts on my blog at http://www.devco.net/

Released under the Apache 2.0 licence

Usage:
------

If you wanted a /etc/motd file that listed all the major modules
on the machine.  And that would be maintained automatically even
if you just remove the include lines for other modules you could
use code like below, a sample /etc/motd would be:

<pre>
Puppet modules on this server:

    -- Apache
    -- MySQL
</pre>

Local sysadmins can also append to the file by just editing /etc/motd.local
their changes will be incorporated into the puppet managed motd.

<pre>
# class to setup basic motd, include on all nodes
class motd {
   $motd = "/etc/motd"

   concat{$motd:
      owner => root,
      group => root,
      mode  => 644
   }

   concat::fragment{"motd_header":
      target => $motd,
      content => "\nPuppet modules on this server:\n\n",
      order   => 01,
   }

   # local users on the machine can append to motd by just creating
   # /etc/motd.local
   concat::fragment{"motd_local":
      target => $motd,
      ensure  => "/etc/motd.local",
      order   => 15
   }
}

# used by other modules to register themselves in the motd
define motd::register($content="", $order=10) {
   if $content == "" {
      $body = $name
   } else {
      $body = $content
   }

   concat::fragment{"motd_fragment_$name":
      target  => "/etc/motd",
      content => "    -- $body\n"
   }
}

# a sample apache module
class apache {
   include apache::install, apache::config, apache::service

   motd::register{"Apache": }
}
</pre>

Known Issues:
-------------
* Since puppet-concat now relies on a fact for the concat directory,
  you will need to set up pluginsync = true for at least the first run.
  You have this issue if puppet fails to run on the client and you have
  a message similar to
  "err: Failed to apply catalog: Parameter path failed: File
  paths must be fully qualified, not 'undef' at [...]/concat/manifests/setup.pp:44".

Contributors:
-------------
**Paul Elliot**

 * Provided 0.24.8 support, shell warnings and empty file creation support.

**Chad Netzer**

 * Various patches to improve safety of file operations
 * Symlink support

**David Schmitt**

 * Patch to remove hard coded paths relying on OS path
 * Patch to use file{} to copy the resulting file to the final destination.  This means Puppet client will show diffs and that hopefully we can change file ownerships now

**Peter Meier**

 * Basedir as a fact
 * Unprivileged user support

**Sharif Nassar**

 * Solaris/Nexenta support
 * Better error reporting

**Christian G. Warden**

 * Style improvements

**Reid Vandewiele**

 * Support non GNU systems by default

**Erik Dalén*

 * Style improvements

**Gildas Le Nadan**

 * Documentation improvements

**Paul Belanger**

 * Testing improvements and Travis support

**Branan Purvine-Riley**

 * Support Puppet Module Tool better

**Dustin J. Mitchell**

 * Always include setup when using the concat define

**Andreas Jaggi**

 * Puppet Lint support

**Jan Vansteenkiste**

 * Configurable paths

Contact:
--------
R.I.Pienaar / rip@devco.net / @ripienaar / http://devco.net
