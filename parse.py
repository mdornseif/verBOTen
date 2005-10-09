#!/usr/bin/python

# reads .ARC files and addt the contents to the database

import sys
import ARCive
import _mysql
import MySQLdb
from sets import Set
from cStringIO import StringIO
from robotparser import RobotFileParser

# aqdd your dbname and password here
conn = MySQLdb.connect (host = "localhost", user = "root", passwd = "", db = "lufgrails_dev")
cursor = conn.cursor()

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
	if len(entries) == 0:
		return
	cursor.execute("select id from archive_hosts where host = %s", host)
	row = cursor.fetchone()
	if row == None:
		# add that row
		row = cursor.fetchone ()
		cursor.execute("INSERT INTO archive_hosts (host) VALUES(%s)", host)
		hostid = cursor.lastrowid
	else:
		hostid = row[0]

	for path in entries:
		cursor.execute("select id from archive_robots_disallows where path = %s", path)
		row = cursor.fetchone()
		if row == None:
			# add that row
			cursor.execute("INSERT INTO archive_robots_disallows (archive_host_id, path) VALUES(%d, '%s')" % (hostid, _mysql.escape_string(path)))
			print host, path

def processfile(filename):
	arc = ARCive.ARCive(filename)

	ret = []
	while 1:
		meta, content = arc.readRawDoc()
		if not content:
			break # done

		if meta['resultcode'] != '200':
			continue
	
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
	
		yield(host.lower(), entries)
	
if __name__ == "__main__":
	if not len(sys.argv) > 1: 
		sys.stderr.write("Usage: %s filename\n" % (sys.argv[0]))
	for infile in sys.argv[1:]:
		print "processing %r:" % infile
		for host, entries in processfile(infile):
			dbinsert(host, entries)

