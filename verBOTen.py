#!/usr/bin/python

import sys
import robotparser
import threading
import time

#datadir = "/tmp/verBOTen/"
datadir = "datadir/"

def handle(host):

	print "handling '%s'" % (host)

	r = robotparser.RobotFileParser()
	r.set_url("http://" + host + "/robots.txt")
	r.read()

	filename = datadir + host
	outfile = open(filename, "w")

	for e in r.entries:
		for rule in e.rulelines:
			if rule.allowance == 0:
				outfile.write(rule.path + "\n")

	outfile.close()


if __name__ == "__main__":

	if len(sys.argv) != 2:
		sys.stderr.write("Usage: %s filename\n", sys.argv[0])

	datafile = open(sys.argv[1])

	#while True:

#		if host_f != "":
#		Threading.Thread(target=handle, args=somehost).start()
#		host = host[:-1]

		#handle(host)
#		Threading.Thread(target=handle, args=somehost).start()
#		Threading.Thread(target=handle, args=somehost).start()
#		Threading.Thread(target=handle, args=somehost).start()
#		Threading.Thread(target=handle, args=somehost).start()

	for line in datafile:
		line = line[:-1]
		#b = threading.Thread(target=handle, kwargs={"host" : line})
		#b.start()

		threading.Thread(target=handle, kwargs={"host" : line}).start()

		while threading.activeCount() > 10:
			time.sleep(1)
