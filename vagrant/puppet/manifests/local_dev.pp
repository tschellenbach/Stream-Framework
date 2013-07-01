notice("provisioning local development setup")

include stdlib
require base_server
include sudoers


node default {
    notice("Running with userdata $ec2_userdata and fqdn $fqdn")
    $role = "local_dev"
    # get the role from the userdata
    if ($userdata) {
      $role = $userdata['role']
    }
    notice("Running with role $role")
    include local_dev
    
      case $role {
        # the main development setup, with example included
        local_dev: { include local_dev }
        # only cassandra
        cassandra: { include cassandra_dev }
      }
}



    
