notice("provisioning local development setup")

include stdlib
require base_server
include sudoers


node default {
    include local_dev
}



    
