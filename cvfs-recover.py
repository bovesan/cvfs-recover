#!/usr/bin/env python

import sys, os, re, struct, gzip

def getuncompressedsize(filename):
    with open(filename, 'rb') as f:
        f.seek(-4, 2)
        return struct.unpack('I', f.read(4))[0]

def path_mount_point(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

usage = """Usage:
recover.py [-n] [--limit=0] directory_with_FOUND_files index_file
"""

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
				print  'Orphan count: %i\r' % i,
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
	sys.exit(1)

print '\n',

lognr = 0
while os.path.isfile(params['log'] % lognr):
	lognr += 1
logfile = params['log'] % lognr
restored_count = 0
error_count = 0
for index in indexes:
	zipped = False
	print 'Looking for matches in ' + index
	if index.endswith('.gz'):
		zipped = True
		index_size = getuncompressedsize(index)
		f = gzip.open(index)
	else:
		index_size = os.path.getsize(index)
		f = open(index)
	parsed_bytes = 0
	print 'Index size: %i' % index_size

	for line in f:
		parsed_bytes += len(line)
		#line_split = line.strip().split()
		#print repr(line)
		line_split = re.split(" +",line.lstrip().rstrip('\n'), 10)
		#print repr(line_split)
		inode_number = int(line_split[0])
		stored_path = volume_root+line_split[-1].decode('string_escape')
		if inode_number in found_files and not os.path.exists(stored_path) and path_mount_point(stored_path) == path_mount_point(found_files[inode_number]):
			parent_dir = os.path.dirname(stored_path)
			if not os.path.isdir(parent_dir):
				try:
					os.makedirs(parent_dir)
					loglinedir = 'Created missing directory: %s\n' % parent_dir
				except OSError as e:
					loglinedir = ('Could not create missing directory: %s ' % parent_dir)+("Error({0}): {1}\n".format(e.errno, e.strerror))
				open(logfile, 'a').write(loglinedir)
				print '\r'+loglinedir,
			logline = ('Inode: %i ' % inode_number).ljust(20)+'%s > %s\n' % (found_files[inode_number], stored_path)
			if not no_apply:
				try:
					os.rename(found_files[inode_number], stored_path)
					logline = 'Restored: '+logline
					restored_count += 1
				except OSError as e:
					logline = "Error({0}): {1} > ".format(e.errno, e.strerror)+logline
					error_count += 1
			print '\r'+logline,
			open(logfile, 'a').write(logline)
		progress = float(parsed_bytes) / float(index_size)
		print  '\r%05.2f%%' % (progress * 100.0),

logline = 'Orphans detected: %i Restored: %i Errors: %i Still nameless: %i\n' % (i, restored_count, error_count, i - restored_count)
print '\n'+logline,
print 'Log file: ' + logfile