postgresql
===========

Table of Contents
-----------------

1. [Overview - What is the PostgreSQL module?](#overview)
2. [Module Description - What does the module do?](#module-description)
3. [Setup - The basics of getting started with PostgreSQL module](#setup)
4. [Usage - How to use the module for various tasks](#usage)
5. [Reference - The classes, defines,functions and facts available in this module](#reference)
6. [Limitations - OS compatibility, etc.](#limitations)
7. [Development - Guide for contributing to the module](#development)
8. [Disclaimer - Licensing information](#disclaimer)
9. [Transfer Notice - Notice of authorship change](#transfer-notice)
10. [Contributors - List of module contributors](#contributors)

Overview
--------

The PostgreSQL module allows you to easily manage postgres databases with Puppet.

Module Description
-------------------

PostgreSQL is a high-performance, free, open-source relational database server. The postgresql module allows you to manage PostgreSQL packages and services on several operating systems, while also supporting basic management of PostgreSQL databases and users. The module offers support for managing firewall for postgres ports on RedHat-based distros, as well as support for basic management of common security settings.

Setup
-----

**What puppetlabs-PostgreSQL affects:**

* package/service/configuration files for PostgreSQL
* listened-to ports
* system firewall (optional)
* IP and mask (optional)

**Introductory Questions**

The postgresql module offers many security configuration settings. Before getting started, you will want to consider:

* Do you want/need to allow remote connections?
    * If yes, what about TCP connections?
* Would you prefer to work around your current firewall settings or overwrite some of them?
* How restrictive do you want the database superuser's permissions to be?

Your answers to these questions will determine which of the module's parameters you'll want to specify values for.

###Configuring the server

The main configuration you’ll need to do will be around the `postgresql::server` class. The default parameters are reasonable, but fairly restrictive regarding permissions for who can connect and from where. To manage a PostgreSQL server with sane defaults:

    include postgresql::server

For a more customized, less restrictive configuration:

    class { 'postgresql::server':
      config_hash => {
        'ip_mask_deny_postgres_user' => '0.0.0.0/32',
        'ip_mask_allow_all_users'    => '0.0.0.0/0',
        'listen_addresses'           => '*',
        'ipv4acls'                   => ['hostssl all johndoe 192.168.0.0/24 cert'],
        'manage_redhat_firewall'     => true,
        'postgres_password'          => 'TPSrep0rt!',
      },
    }

Once you've completed your configuration of `postgresql::server`, you can test out your settings from the command line:

    $ psql -h localhost -U postgres
    $ psql -h my.postgres.server -U

If you get an error message from these commands, it means that your permissions are set in a way that restricts access from where you’re trying to connect. That might be a good thing or a bad thing, depending on your goals.

Advanced configuration setting parameters can be placed into `postgresql_puppet_extras.conf` (located in the same folder as `postgresql.conf`). You can manage that file as a normal puppet file resource, or however you see fit; which gives you complete control over the settings. Any value you specify in that file will override any existing value set in the templated version.

For more details about server configuration parameters consult the [PostgreSQL Runtime Configuration docs](http://www.postgresql.org/docs/9.2/static/runtime-config.html).

Usage
-----

###Creating a database

There are many ways to set up a postgres database using the `postgresql::db` class. For instance, to set up a database for PuppetDB (this assumes you’ve already got the `postgresql::server` set up to your liking in your manifest, as discussed above):

    postgresql::db { 'mydatabasename':
      user     => 'mydatabaseuser',
      password => 'mypassword'
    }

###Managing users, roles and permissions

To manage users, roles and permissions:

    postgresql::database_user{'marmot':
      password => 'foo',
    }

    postgresql::database_grant{'test1':
      privilege   => 'ALL',
      db          => 'test1',
      role        => 'dan',
    }

In this example, you would grant ALL privileges on the test1 database to the user or group specified by dan.

At this point, you would just need to plunk these database name/username/password values into your PuppetDB config files, and you are good to go.

Reference
---------

The postgresql module comes with many options for configuring the server. While you are unlikely to use all of the below settings, they allow you a decent amount of control over your security settings.

Classes:

* [postgresql](#class-postgresql)
* [postgresql::server](#class-postgresqlserver)
* [postgresql::client](#class-postgresqlclient)
* [postgresql::contrib](#class-postgresqlcontrib)
* [postgresql::devel](#class-postgresqldevel)
* [postgresql::java](#class-postgresqljava)
* [postgresql::python](#class-postgresqlpython)

Resources:

* [postgresql::db](#resource-postgresqldb)
* [postgresql::database](#resource-postgresqldatabase)
* [postgresql::database_grant](#resource-postgresqldatabasegrant)
* [postgresql::role](#resource-postgresqlrole)
* [postgresql::tablespace](#resource-postgresqltablespace)
* [postgresql::validate_db_connection](#resource-postgresqlvalidatedbconnection)
* [postgresql::pg_hba_rule](#resource-postgresqlpghbarule)

Functions:

* [postgresql\_password](#function-postgresqlpassword)
* [postgresql\_acls\_to\_resources\_hash](#function-postgresqlaclstoresourceshashaclarray-id-orderoffset)

Facts:

* [postgres\_default\_version](#fact-postgresdefaultversion)

###Class: postgresql
This class is used to configure the main settings for this module, to be used by the other classes and defined resources. On its own it does nothing.

For example, if you wanted to overwrite the default `locale` and `charset` you could use the following combination:

    class { 'postgresql':
      charset => 'UTF8',
      locale  => 'en_NG',
    }->
    class { 'postgresql::server':
    }

That would make the `charset` and `locale` the default for all classes and defined resources in this module.

####`version`
The version of PostgreSQL to install/manage. Defaults to your operating system default.

####`manage_package_repo`
If `true` this will setup the official PostgreSQL repositories on your host. Defaults to `false`.

####`locale`
This will set the default database locale for all databases created with this module. On certain operating systems this will be used during the `template1` initialization as well so it becomes a default outside of the module as well. Defaults to `undef` which is effectively `C`.

####`charset`
This will set the default charset for all databases created with this module. On certain operating systems this will be used during the `template1` initialization as well so it becomes a default outside of the module as well. Defaults to `UTF8`.

####`datadir`
This setting can be used to override the default postgresql data directory for the target platform. If not specified, the module will use whatever directory is the default for your OS distro.

####`confdir`
This setting can be used to override the default postgresql configuration directory for the target platform. If not specified, the module will use whatever directory is the default for your OS distro.

####`bindir`
This setting can be used to override the default postgresql binaries directory for the target platform. If not specified, the module will use whatever directory is the default for your OS distro.

####`client_package_name`
This setting can be used to override the default postgresql client package name. If not specified, the module will use whatever package name is the default for your OS distro.

####`server_package_name`
This setting can be used to override the default postgresql server package name. If not specified, the module will use whatever package name is the default for your OS distro.

####`contrib_package_name`
This setting can be used to override the default postgresql contrib package name. If not specified, the module will use whatever package name is the default for your OS distro.

####`devel_package_name`
This setting can be used to override the default postgresql devel package name. If not specified, the module will use whatever package name is the default for your OS distro.

####`java_package_name`
This setting can be used to override the default postgresql java package name. If not specified, the module will use whatever package name is the default for your OS distro.

####`service_name`
This setting can be used to override the default postgresql service name. If not specified, the module will use whatever service name is the default for your OS distro.

####`user`
This setting can be used to override the default postgresql super user and owner of postgresql related files in the file system. If not specified, the module will use the user name 'postgres'.

####`group`
This setting can be used to override the default postgresql user group to be used for related files in the file system. If not specified, the module will use the group name 'postgres'.

####`run_initdb`
This setting can be used to explicitly call the initdb operation after server package is installed and before the postgresql service is started. If not specified, the module will decide whether to call initdb or not depending on your OS distro.

###Class: postgresql::server
Here are the options that you can set in the `config_hash` parameter of `postgresql::server`:

####`postgres_password`
This value defaults to `undef`, meaning the super user account in the postgres database is a user called `postgres` and this account does not have a password. If you provide this setting, the module will set the password for the `postgres` user to your specified value.

####`listen_addresses`
This value defaults to `localhost`, meaning the postgres server will only accept connections from localhost. If you’d like to be able to connect to postgres from remote machines, you can override this setting. A value of `*` will tell postgres to accept connections from any remote machine. Alternately, you can specify a comma-separated list of hostnames or IP addresses. (For more info, have a look at the `postgresql.conf` file from your system’s postgres package).

####`manage_redhat_firewall`
This value defaults to `false`. Many RedHat-based distros ship with a fairly restrictive firewall configuration which will block the port that postgres tries to listen on. If you’d like for the puppet module to open this port for you (using the [puppetlabs-firewall](http://forge.puppetlabs.com/puppetlabs/firewall) module), change this value to true. *[This parameter is likely to change in future versions.  Possible changes include support for non-RedHat systems and finer-grained control over the firewall rule (currently, it simply opens up the postgres port to all TCP connections).]*

####`ip_mask_allow_all_users`
This value defaults to `127.0.0.1/32`. By default, Postgres does not allow any database user accounts to connect via TCP from remote machines. If you’d like to allow them to, you can override this setting. You might set it to `0.0.0.0/0` to allow database users to connect from any remote machine, or `192.168.0.0/16` to allow connections from any machine on your local 192.168 subnet.

####`ip_mask_deny_postgres_user`
This value defaults to `0.0.0.0/0`. Sometimes it can be useful to block the superuser account from remote connections if you are allowing other database users to connect remotely. Set this to an IP and mask for which you want to deny connections by the postgres superuser account. So, e.g., the default value of `0.0.0.0/0` will match any remote IP and deny access, so the postgres user won’t be able to connect remotely at all. Conversely, a value of `0.0.0.0/32` would not match any remote IP, and thus the deny rule will not be applied and the postgres user will be allowed to connect.

####`pg_hba_conf_path`
If, for some reason, your system stores the `pg_hba.conf` file in a non-standard location, you can override the path here.

####`postgresql_conf_path`
If, for some reason, your system stores the `postgresql.conf` file in a non-standard location, you can override the path here.

####`ipv4acls`
List of strings for access control for connection method, users, databases, IPv4 addresses; see [postgresql documentation](http://www.postgresql.org/docs/9.2/static/auth-pg-hba-conf.html) about `pg_hba.conf` for information (please note that the link will take you to documentation for the most recent version of Postgres, however links for earlier versions can be found on that page).

####`ipv6acls`
List of strings for access control for connection method, users, databases, IPv6 addresses; see [postgresql documentation](http://www.postgresql.org/docs/9.2/static/auth-pg-hba-conf.html) about `pg_hba.conf` for information (please note that the link will take you to documentation for the most recent version of Postgres, however links for earlier versions can be found on that page).

###Class: postgresql::client

This class installs postgresql client software. Alter the following parameters if you have a custom version you would like to install (Note: don't forget to make sure to add any necessary yum or apt repositories if specifying a custom version):

####`package_name`
The name of the postgresql client package.

####`package_ensure`
The ensure parameter passed on to postgresql client package resource.

###Class: postgresql::contrib
Installs the postgresql contrib package.

####`package_name`
The name of the postgresql client package.

####`package_ensure`
The ensure parameter passed on to postgresql contrib package resource.

###Class: postgresql::devel
Installs the packages containing the development libraries for PostgreSQL.

####`package_ensure`
Override for the `ensure` parameter during package installation. Defaults to `present`.

####`package_name`
Overrides the default package name for the distribution you are installing to. Defaults to `postgresql-devel` or `postgresql<version>-devel` depending on your distro.

###Class: postgresql::java
This class installs postgresql bindings for Java (JDBC). Alter the following parameters if you have a custom version you would like to install (Note: don't forget to make sure to add any necessary yum or apt repositories if specifying a custom version):

####`package_name`
The name of the postgresql java package.

####`package_ensure`
The ensure parameter passed on to postgresql java package resource.

###Class: postgresql::python
This class installs the postgresql Python libraries. For customer requirements you can customise the following parameters:

####`package_name`
The name of the postgresql python package.

####`package_ensure`
The ensure parameter passed on to postgresql python package resource.

###Resource: postgresql::db
This is a convenience resource that creates a database, user and assigns necessary permissions in one go.

For example, to create a database called `test1` with a corresponding user of the same name, you can use:

    postgresql::db { 'test1':
      user     => 'test1',
      password => 'test1',
    }

####`namevar`
The namevar for the resource designates the name of the database.

####`user`
User to create and assign access to the database upon creation. Mandatory.

####`password`
Password for the created user. Mandatory.

####`tablespace`
The name of the tablespace to allocate this database to. If not specifies, it defaults to the PostgreSQL default.

####`charset`
Override the character set during creation of the database. Defaults to the default defined during installation.

####`locale`
Override the locale during creation of the database. Defaults to the default defined during installation.

####`grant`
Grant permissions during creation. Defaults to `ALL`.

###Resource: postgresql::database
This defined type can be used to create a database with no users and no permissions, which is a rare use case.

####`namevar`
Name of the database to create.

####`tablespace`
Tablespace for where to create this database. Defaults to the defaults defined during PostgreSQL installation.

####`charset`
Override the character set during creation of the database. Defaults to the default defined during installation.

####`locale`
Override the locale during creation of the database. Defaults to the default defined during installation.

###Resource: postgresql::database\_grant
This defined type manages grant based access privileges for users. Consult the PostgreSQL documentation for `grant` for more information.

####`namevar`
Used to uniquely identify this resource, but functionality not used during grant.

####`privilege`
Can be one of `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES`, `TRIGGER`, `USAGE`, `TEMPORARY`, `TEMP`, `CONNECT`. `ALL` is used as a synonym for `CREATE`. If you need to add multiple privileges, a space delimited string can be used.

####`db`
Database to grant access to.

####`role`
Role or user whom you are granting access for.

####`psql_db`
Database to execute the grant against. This should not ordinarily be changed from the default, which is `postgres`.

####`psql_user`
OS user for running `psql`. Defaults to the default user for the module, usually `postgres`.

###Resource: postgresql::role
This resource creates a role or user in PostgreSQL.

####`namevar`
The role name to create.

####`password_hash`
The hash to use during password creation. Use the `postgresql_password` function to provide an MD5 hash here.

####`createdb`
Weither to grant the ability to create new databases with this role. Defaults to `false`.

####`createrole`
Weither to grant the ability to create new roles with this role. Defaults to `false`.

####`login`
Weither to grant login capability for the new role. Defaults to `false`.

####`superuser`
Weither to grant super user capability for the new role. Defaults to `false`.

####`replication`
If `true` provides replication capabilities for this role. Defaults to `false`.

####`connection_limit`
Specifies how many concurrent connections the role can make. Defaults to `-1` meaning no limit.

###Resource: postgresql::tablespace
This defined type can be used to create a tablespace. For example:

    postgresql::tablespace{ 'tablespace1':
      location => '/srv/space1',
    }

It will create the location if necessary, assigning it the same permissions as your
PostgreSQL server.

####`namevar`
The tablespace name to create.

####`location`
The path to locate this tablespace.

####`owner`
The default owner of the tablespace.

###Resource: postgresql::validate\_db\_connection
This resource can be utilised inside composite manifests to validate that a client has a valid connection with a remote PostgreSQL database. It can be ran from any node where the PostgreSQL client software is installed to validate connectivity before commencing other dependent tasks in your Puppet manifests, so it is often used when chained to other tasks such as: starting an application server, performing a database migration.

Example usage:

    postgresql::validate_db_connection { 'validate my postgres connection':
      database_host           => 'my.postgres.host',
      database_username       => 'mydbuser',
      database_password       => 'mydbpassword',
      database_name           => 'mydbname',
    }->
    exec { 'rake db:migrate':
      cwd => '/opt/myrubyapp',
    }

####`namevar`
Uniquely identify this resource, but functionally does nothing.

####`database_host`
The hostname of the database you wish to test.

####`database_port`
Port to use when connecting.

####`database_name`
The name of the database you wish to test.

####`database_username`
Username to connect with.

####`database_password`
Password to connect with. Can be left blank, but that is not recommended.

###Resource: postgresql::pg\_hba\_rule
This defined type allows you to create an access rule for `pg_hba.conf`. For more details see the [PostgreSQL documentation](http://www.postgresql.org/docs/8.2/static/auth-pg-hba-conf.html).

For example:

    postgresql::pg_hba_rule { 'allow application network to access app database':
      description => "Open up postgresql for access from 200.1.2.0/24",
      type => 'host',
      database => 'app',
      user => 'app',
      address => '200.1.2.0/24',
      auth_method => 'md5',
    }

This would create a ruleset in `pg_hba.conf` similar to:

    # Rule Name: allow application network to access app database
    # Description: Open up postgresql for access from 200.1.2.0/24
    # Order: 150
    host  app  app  200.1.2.0/24  md5

####`namevar`
A unique identifier or short description for this rule. The namevar doesn't provide any functional usage, but it is stored in the comments of the produced `pg_hba.conf` so the originating resource can be identified.

####`description`
A longer description for this rule if required. Defaults to `none`. This description is placed in the comments above the rule in `pg_hba.conf`.

####`type`
The type of rule, this is usually one of: `local`, `host`, `hostssl` or `hostnossl`.

####`database`
A comma separated list of databases that this rule matches.

####`user`
A comma separated list of database users that this rule matches.

####`address`
If the type is not 'local' you can provide a CIDR based address here for rule matching.

####`auth_method`
The `auth_method` is described further in the `pg_hba.conf` documentation, but it provides the method that is used for authentication for the connection that this rule matches.

####`auth_option`
For certain `auth_method` settings there are extra options that can be passed. Consult the PostgreSQL `pg_hba.conf` documentation for further details.

####`order`
An order for placing the rule in `pg_hba.conf`. Defaults to `150`.

####`target`
This provides the target for the rule, and is generally an internal only property. Use with caution.

###Function: postgresql\_password
If you need to generate a postgres encrypted password, use `postgresql_password`. You can call it from your production manifests if you don't mind them containing the clear text versions of your passwords, or you can call it from the command line and then copy and paste the encrypted password into your manifest:

    $ puppet apply --execute 'notify { "test": message => postgresql_password("username", "password") }'

###Function: postgresql\_acls\_to\_resources\_hash(acl\_array, id, order\_offset)
This internal function converts a list of `pg_hba.conf` based acls (passed in as an array of strings) to a format compatible with the `postgresql::pg_hba_rule` resource.

**This function should only be used internally by the module**.

###Fact: postgres\_default\_version
The module provides a Facter fact that can be used to determine what the default version of postgres is for your operating system/distribution. Depending on the distribution, it might be 8.1, 8.4, 9.1, or possibly another version. This can be useful in a few cases, like when building path strings for the postgres directories.

Limitations
------------

Works with versions of PostgreSQL from 8.1 through 9.2.

Development
------------

Puppet Labs modules on the Puppet Forge are open projects, and community contributions are essential for keeping them great. We can't access the huge number of platforms and myriad of hardware, software, and deployment configurations that Puppet is intended to serve.

We want to keep it as easy as possible to contribute changes so that our modules work in your environment. There are a few guidelines that we need contributors to follow so that we can have a chance of keeping on top of things.

You can read the complete module contribution guide [on the Puppet Labs wiki.](http://projects.puppetlabs.com/projects/module-site/wiki/Module_contributing)

### Tests

There are two types of tests distributed with the module. The first set is the 'traditional' Puppet manifest-style smoke tests. You can use these to experiment with the module on a virtual machine or other test environment, via `puppet apply`. You should see the following files in the `tests` directory.

In addition to these manifest-based smoke tests, there are some ruby rspec tests in the spec directory. These tests run against a VirtualBox VM, so they are actually testing the live application of the module on a real, running system. To do this, you must install and setup an [RVM](http://beginrescueend.com/) with [vagrant](http://vagrantup.com/), [sahara](https://github.com/jedi4ever/sahara), and [rspec](http://rspec.info/):

    $ curl -L get.rvm.io | bash -s stable
    $ rvm install 1.9.3
    $ rvm use --create 1.9.3@puppet-postgresql
    $ bundle install

Run the system tests:

    $ rake spec:system

The system test suite will snapshot the VM and rollback between each test. If you want to only run the tests against an individual distro, you can do run:

    $ rspec spec/distros/ubuntu_lucid_64

We also have some unit tests that utilize rspec-puppet for faster iteration if required:

    $ rake spec

The unit tests are ran in Travis-CI as well, if you want to see the results of your own tests regsiter the service hook through Travis-CI via the accounts section for your Github clone of this project.

Transfer Notice
----------------

This Puppet module was originally authored by Inkling Systems. The maintainer preferred that Puppet Labs take ownership of the module for future improvement and maintenance as Puppet Labs is using it in the PuppetDB module.  Existing pull requests and issues were transferred over, please fork and continue to contribute here instead of Inkling.

Previously: [https://github.com/inkling/puppet-postgresql](https://github.com/inkling/puppet-postgresql)

Contributors
------------

 * Andrew Moon
 * [Kenn Knowles](https://github.com/kennknowles) ([@kennknowles](https://twitter.com/KennKnowles))
 * Adrien Thebo
 * Albert Koch
 * Andreas Ntaflos
 * Brett Porter
 * Chris Price
 * dharwood
 * Etienne Pelletier
 * Florin Broasca
 * Henrik
 * Hunter Haugen
 * Jari Bakken
 * Jordi Boggiano
 * Ken Barber
 * nzakaria
 * Richard Arends
 * Spenser Gilliland
 * stormcrow
 * William Van Hevelingen
