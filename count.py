#!/usr/bin/env python

import sys, os, time
from scandir import scandir, walk

usage = """Usage:
count.py [-d] [-r] [files...] [folders...]"""

def f2(n):
    r = []
    for i, c in enumerate(reversed(str(n))):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    return ''.join(r)


def get_terminal_size():
	rows, columns = os.popen('stty size', 'r').read().split()
	class terminal_size:
		y = int(rows)
		x = int(columns)
	return terminal_size

def count(path, recursive=False, delete=False):
	global counter
	for entry in scandir(path):
		counter += 1
		if delete and entry.path.startswith(path):
			print "\nRemoving: " + entry.path,
			time.sleep(0.1) # Trying to ease the system load
			try:
				#os.remove(entry.path)
				print 'delete'
			except OSError as e:
				print " Error({0}): {1}".format(e.errno, e.strerror)
		if recursive and entry.is_dir(follow_symlinks=False):
			count(entry.path, recursive, delete)
		if sys.stdout.isatty():
			line = ('%s %s' % (str(counter).ljust(20), path))[-width:].ljust(width) + '\r'
			print  line,
		else:
			line = ('%s %s' % (str(i+counter).ljust(20), path))[-width:].ljust(width) + '\r'
			sys.stderr.write(line)
			sys.stderr.flush()

i = 0
delete = False
recursive = False
quiet = False
width = get_terminal_size().x
for arg in sys.argv[1:]:
	if arg.startswith('-'):
		for char in arg[1:]:
			if char == 'd':
				delete = True
			elif char == 'r':
				recursive = True
			elif char == 'q':
				quiet = True
	elif os.path.isdir(arg):
		counter = 1
		count(arg, recursive, delete)
		width = get_terminal_size().x
		print  ('%s %s' % (str(counter).ljust(20), arg)).ljust(width)
		i += counter
	else:
		i += 1
		if not quiet:
			print (''.ljust(21)) + arg

print 'Total: ' + f2(i)
if not sys.stdout.isatty():
	sys.stderr.write('\n')
	sys.stderr.flush()
