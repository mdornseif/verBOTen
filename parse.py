#!/usr/bin/python

import sys
import ARCive
#import _mysql
#import MySQLdb
from sets import Set
from cStringIO import StringIO
from robotparser import RobotFileParser

class MyRobotFileParser(RobotFileParser):
	def __init__(self, file=None):
		RobotFileParser.__init__(self)
		self._file = file

	def read(self):
		from string import strip
		lines = self._file.readlines()
		map(strip, lines)
		self.parse(lines)


def dbinsert(host, entries):

#	crs.execute("INSERT INTO hosts (host) VALUES(%s)" % (_mysql.escape_string(filename)))
#	hostid = crs.lastrowid

	for entry in entries:
#		crs.execute("INSERT INTO entries (host_id, path) VALUES(%d, '%s')" % (hostid, _mysql.escape_string(entry)))
		print entry

def processfile(filename):
	file = ARCive.ARCive(filename)

	meta, content = file.readRawDoc()

	if meta['resultcode'] != '200':
		return

	host = meta['url'].split('/')[2]

	c = content.split("\r\n\r\n")
	if len(c) > 1:
		# separate header from bdoy
		body = "".join(c[1:])
	else:
		# there are no headers
		body = c[0]

	entries = Set()

	r = MyRobotFileParser(StringIO(body))
	r.read()

	for e in r.entries:
		for rule in e.rulelines:
			if rule.allowance == 0:
				entries.add(rule.path)

	return host, entries

if __name__ == "__main__":
	if len(sys.argv) != 2: 
		sys.stderr.write("Usage: %s filename\n" % (sys.argv[0]))

	host, entries = processfile(sys.argv[1])
	dbinsert(host, entries)

