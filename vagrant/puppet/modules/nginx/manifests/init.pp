class nginx {

    file { "/opt/nginx":
        ensure  => "directory",
    }
   
	package { 'nginx':
	     ensure => present,
	}
	  
    service { "nginx":
        enable    => "true",
        ensure    => "running",
        require   => File["/etc/nginx"],
    }

    file { "/etc/nginx":
        ensure => "directory",
        source => "puppet:///modules/nginx/nginx_conf_dir",
        recurse => "true",
        require => Package["nginx"],
        notify => Service["nginx"],
    }
}
