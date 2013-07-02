notice("provisioning local development setup")

include stdlib
require base_server
include sudoers


node default {
    notice("Running with userdata $ec2_userdata and fqdn $fqdn")
    
    # get the role from the userdata
    if ($ec2_userdata) {
      $userdata = parsejson($ec2_userdata)
      $role = $userdata['role']
    } else {
      $role = "local_dev"
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



    
