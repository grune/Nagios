#!/usr/bin/python
################### check_nt_mssql_database.py ##################
# Version :     1.0.0
# Date :        May 8th 2012
# Author  :     Rick Rune (rick at runeg dot net)
# Help :        rick at runeg dot net
# Licence :     GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog:
# Requires:     NSClient++ & SQL Server with Perfmon Counters
# Location:     /usr/lib/nagios/plugins/check_mssql_mem (on Debian based systems)
# Install:      Copy to Location, chmod +x ./check_mssql_mem
#
# Config File:  /etc/nagios-plugins/config/check_mssql_mem.cfg
### 'check_mssqlmem' command definition
#define command{
#        command_name    check_mssql_mem
#        command_line    /usr/lib/nagios/plugins/check_mssql_mem -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$
#}
#
# How to call out as a service:
##define service{
#        use                     generic-service
#        host_name               winserver
#        service_description     check mssql mem
#        check_command           check_mssql_mem!80!90
#        }
#

##################################################################
def main():
    # Standard imports.
    from sys import exit
    from optparse import OptionParser
    from subprocess import Popen, PIPE, call
 
    # This location works for Debian based servers using default installation dirs.
    check_nt = "/usr/lib/nagios/plugins/check_nt"
 
    #Option Parser diaglogues.
    usage = "Nagios plugin for querying against Windows Perfmon."
    option_dialogue = 'db_memory_calc: Calculates SQL Memory in use\
                     db_pages_used: Pages in use in MB\
                     db_pages_total: Total pages in MB'
    
    # Options all in lowercase.
    option_list =   {
         'db_pages_used': "\\SQLServer:Buffer Manager\\Database pages",
         'db_pages_total': "\\SQLServer:Buffer Manager\\Total pages",
         'db_memory_calc': 'db_memory_calc',
         }

    # Standard way to exit script.
    def sys_exit(status_message, exit_code):
        print status_message
        exit(exit_code)

    # Simple wrapper around sub_process.Popen
    def sub_proc(command):
        try:
            proc = Popen(command, stdout=PIPE)
            output = proc.stdout.readlines()
            proc.stdout.close()
            return output
        except OSError, err:
            sys_exit('Error executing Check_NT. \n(sub_proc.Popen() \
                     exception running "%s": %s)' % (command, err), -1)

    # Calculating threshold results.
    def calculate_threshold(value, warn, crit):
        # For interger comparison
        value = int(value)
        warn = int(warn)
        crit = int(crit)
       
        # For services no thresholds.
        if [warn, crit] == [0, 0]:
            return 0 #'OK:'
        
        if value < warn:
            return 0 # OK
        elif warn <= value < crit:
         return 1 # WARNING
        elif crit <= value:
           return 2 # CRITICAL
        else:
            return -1 # UNKNOWN

    # Execute sub_process against check_nt with derived variables.
    def use_check_nt(Type, check_nt, hostname, port, option, warning, critical):
        defined_command = [check_nt,
                           '-H', hostname,
                           '-p', port,
                           '-v', 'COUNTER',
                           '-l', option, '-w', warning, '-c', critical]
        if option == "db_memory_calc":
            return db_memory_calc(check_nt, hostname, port, option, warning, critical)
        else:
            results = sub_proc(defined_command)
            return results[0]
 
    # Returns data to Nagios related to option.
    def returned_results(option, option_output, query_results, warning, critical):
        # Setting Threshold response.
        threshold_status = calculate_threshold(query_results[0], warning, critical)
 
        # Used for any Page based counters
        if option_output == 'pageconvert':
            # Converting page (1 Page = 8Kbytes) to byte to MByte.
            try: converted = ((int(query_results)*8)/1024)
            except: sys_exit("error: 101: Interger conversion error using: %s"
                             % query_results, -1)
            sys_exit("%s: %s MB" % (option, converted), threshold_status)
 
        # Used for any percentrage based counters.
        elif option_output == 'perc':
            sys_exit("%i %s: %s%%" % (option, query_results), threshold_status)
 
        # Used to calculate used SQL memory vs total SQL memory.
        elif option_output == 'db_memory_calc':
            # Clarity for exit string.
            memPerc = query_results[0]
            used_mem = query_results[1]
            total_mem = query_results[2]
            sys_exit(("SQL Memory usage: %.2f%% (%.0f MB Used / %.0f MB Total) |\
                      'SQL Memory usage'=%.2f;%s.00;%s.00;0;100;\n" \
                    % (memPerc, used_mem, total_mem, memPerc, warning,
                       critical)), threshold_status)
 
    # Determines how to manipulate selected option.
    def option_output(option):
        if option.startswith("db_pages_"):
            return 'pageconvert'
        elif option in ['db_memory_calc']:
            return 'db_memory_calc'
        else: return 'base'
 
    # Returns used memory as percentage. Calculates used/total pages from SQL counters.
    def db_memory_calc(check_nt, hostname, port, option, warning_calc_value, critical_calc_value):
        total_mem = float(use_check_nt('pageconvert', check_nt, hostname, port, option_list['db_pages_total'], warning_calc_value, critical_calc_value))
        used_mem = float(use_check_nt('pageconvert', check_nt, hostname, port, option_list['db_pages_used'], warning_calc_value, critical_calc_value))
        # Gaining used memory and converting X.XX% to XX%
        mem_results  = (used_mem/total_mem)*100
        return [mem_results, ((used_mem*8)/1024), ((total_mem*8)/1024)]
 
    # Argument parser.
    parser = OptionParser(usage=usage)
    # Argument list.
    parser.add_option('-H', '--hostname', help='Specify hostname or IP Address', default=False)
    parser.add_option('-p', '--port', help='Specify port. [Default: 12489]', default='12489')
    parser.add_option('-o', '--option', help=option_dialogue, default='db_memory_calc')
    parser.add_option('-w', '--warning', help='Specify min or max threshold', default='0')
    parser.add_option('-c', '--critical', help='Specify min or max threshold', default='0')
 
    # Making options a dictionary for easier manipulation.
    (options, args) = parser.parse_args()
    index = options.__dict__
 
    # Breaking down arguments.
    hostname = index['hostname']
    port = index['port']
    option = index['option'].lower()
    warning = str(index['warning'])
    critical = str(index['critical'])
 
    # Catch for non-existant options.
    if option not in option_list.keys():
        sys_exit("Error: \tMethod \"%s\" not in Method List." % option, -1)
 
    type_results = option_output(option)
    query_results = use_check_nt(type_results, check_nt, hostname, port, option_list[option], warning, critical)
    returned_results(option, type_results, query_results, warning, critical)

if __name__ == '__main__':
   main()