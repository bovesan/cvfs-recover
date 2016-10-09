#!/usr/bin/env python

import sys, os, re

usage = """Usage:
recover.py [-n] [--limit=0] directory_with_FOUND_files volume_index_file

or from an existing log file (made with -n):
recover.py -p [recover.log]"""

found_files = {}
i = 0
indexes = []
logs = []
params = {}
params['limit'] = 0
volume_root = '/Volumes/'
params['log'] = 'recover.%i.log'
no_apply = False
search_mode = True
for arg in sys.argv[1:]:
	if arg.startswith('--'):
		key, value = arg[2:].split('=')
		params[key] = int(value)
	elif arg == '-n':
		no_apply = True
	elif arg == '-p':
		search_mode = False
	elif os.path.isdir(arg):
		for name in os.listdir(arg):
			if name.startswith('FOUND'):
				i += 1
				full_path = os.path.join(arg, name)
				inode_number = os.stat(full_path).st_ino
				found_files[inode_number] = full_path
				print  'FOUND* count: %i\r' % i,
				if i == params['limit']:
					print '\nReached limit\r',
					break
	elif os.path.isfile(arg):
		if search_mode:
			indexes.append(arg)
		else:
			logs.append(arg)

if len(logs) == 0 and ( len(indexes) == 0 or len(found_files) == 0 ):
	print usage

print '\n'

lognr = 0
while os.path.isfile(params['log'] % lognr):
	lognr += 1
logfile = params['log'] % lognr

for index in indexes:
	print 'Looking for matches in ' + index
	index_size = os.path.getsize(index)
	parsed_bytes = 0
	print 'Index size: %i' % index_size
	for line in open(index):
		parsed_bytes += len(line)
		#line_split = line.strip().split()
		#print repr(line)
		line_split = re.split(" +",line.lstrip().rstrip('\n'), 10)
		#print repr(line_split)
		inode_number = int(line_split[0])
		stored_path = volume_root+line_split[-1].decode('string_escape')
		if inode_number in found_files and not os.path.exists(stored_path):
			logline = ('Inode: %i ' % inode_number).ljust(20)+'%s > %s\n' % (found_files[inode_number], stored_path)
			print logline,
			if not no_apply:
				try:
					os.rename(found_files[inode_number], stored_path)
					print 'Moved'
					logline = 'Restored: '+logline
				except OSError as e:
					logline = "Error({0}): {1} > ".format(e.errno, e.strerror)+logline
					print "I/O error({0}): {1}".format(e.errno, e.strerror)
			open(logfile, 'a').write(logline)
		progress = float(parsed_bytes) / float(index_size)
		print  '\r%05.2f%%' % (progress * 100.0),

print 'Log file: ' + logfile