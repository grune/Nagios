#!/usr/bin/python 
#http://oss.oetiker.ch/rrdtool/doc/rrdgraph_examples.en.html
# Static Arguments
rrdtool = "/usr/bin/rrdtool"
report_dir = "/media/reports"
 
import argparse
parser = argparse.ArgumentParser(description='')

parser.add_argument('-i', '--internal', type=str, default=None, nargs='?')
parser.add_argument('-e', '--external', type=str, default=None, nargs='?')
parser.add_argument('-o', '--output', type=str, default=report_dir, nargs='?')

  
args = parser.parse_args()
external_file = args.external
internal_file = args.internal
output_dir = args.output

import datetime
today = datetime.date.today()
week = datetime.timedelta(days=-7)
today_minus_7d = today + week


color = {}
color['red'] = "#FF0000"
color['green'] = "#00FF00"
color['blue'] = "#0000FF"
color['black'] = "#000000"

# passed arguments
customer_id = "foobar"
random_id = "1234"
if args.external == None:
    out_file = "nova.rrd"
else:
    out_file = args.external
if args.internal == None:
    in_file = "runeg.rrd"
else:
    in_file = args.internal

# Generated Variables
save_file = report_dir + "/" + customer_id + "/graph.png"
# with random ID
#save_file = report_dir + "/" + customer_id + "/" + random_id + "graph.png"

graph_title = '%s Report - Date: %s to %s' % (customer_id, today_minus_7d, today)

# RRD command details
def_in = "DEF:in=%s:data:AVERAGE" % in_file
def_out = "DEF:out=%s:data:AVERAGE" % out_file
rrd_cdef = "CDEF:out_neg=out,-1,*"
line1 = 'AREA:in%s:Internal'  % color["blue"]
line2 = 'AREA:out_neg%s:External' % color["red"]
start = "%s" % today_minus_7d
end = "%s" % today

# Command list for subprocess
command = []
command.append(rrdtool)
command.append("graph")
command.append(save_file)

command.append(def_in)
command.append(def_out)
command.append(rrd_cdef)
command.append("--title")
command.append(graph_title)
command.append("--start")
command.append(str(start).replace("-",""))
command.append("--end")
command.append(str(end).replace("-",""))

command.append('COMMENT:           ')
command.append('COMMENT:Maximum    ')
command.append('COMMENT:Average    ')
command.append('COMMENT:Minimum    \l')

command.append(line1)
command.append("VDEF:inavg=in,AVERAGE")
command.append("VDEF:inmax=in,MAXIMUM")
command.append("VDEF:inmin=in,MINIMUM")
command.append('GPRINT:inmax:%6.2lf %Ssec')
command.append('GPRINT:inavg:%6.2lf %Ssec')
command.append('GPRINT:inmin:%6.2lf %Ssec\l')

command.append(line2)
command.append("VDEF:outavg=out,AVERAGE")
command.append("VDEF:outmax=out,MAXIMUM")
command.append("VDEF:outmin=out,MINIMUM")
command.append('GPRINT:outmax:%6.2lf %Ssec')
command.append('GPRINT:outavg:%6.2lf %Ssec')
command.append('GPRINT:outmin:%6.2lf %Ssec\l')

import subprocess
    
proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = proc.communicate()
print output
print err