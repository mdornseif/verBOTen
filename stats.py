#!/usr/bin/python

import sys
import os
import ARCive
import re

def getErrorCodes(directory):
	codes = {}

	for filename in os.listdir(directory):
		file = ARCive.ARCive(filename)
		meta, content = file.readRawDoc()

		status = meta['resultcode']
		if codes.has_key(status):
			codes[status] += 1
		else:
			codes[status] = 1

	return codes

def findInvalidFiles(directory):
	filenames = []

	empty = re.compile("^\s*$")
	comment = re.compile("^\s*#.*", re.M)
	useragent = re.compile("^\s*User-agent:.*", re.M)
	allow = re.compile("^\s*Allow:.*", re.M)
	deny = re.compile("^\s*Disallow:.*", re.M)

	wrongallow = re.compile("^\sAllow:.*\*")
	wrongdeny = re.compile("^\sDisallow:.*\*")

	for filename in os.listdir(directory):
		file = ARCive.ARCive(filename)
		meta, content = file.readRawDoc()

		c = content.split("\r\n\r\n")
		if len(c) > 1:
			# separate header from bdoy
			body = "".join(c[1:])
		else:
			# there are no headers
			body = c[0]


		for line in body.split("\n"):

			if empty.search(line):
				continue

			if wrongallow.search(line) or wrongdeny.search(line):
				filenames.append(filename)
				break

			if comment.search(line) or useragent.search(line) or allow.search(line) or deny.search(line):
				continue

			filenames.append(filename)
			break

	return filenames

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.stderr.write("Usage: %s directory\n" % (sys.argv[0]))
		sys.exit()


	errorCodes = getErrorCodes(sys.argv[1])
	print errorCodes

	invalids = findInvalidFiles(sys.argv[1])
	print invalids
