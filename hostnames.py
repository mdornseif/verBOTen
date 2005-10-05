#!/usr/bin/python

import string

def gen3(filename, tld):
	outfile = open(filename, "w")
	for a in string.lowercase:
		for b in string.lowercase:
			for c in string.lowercase:
				hostname = a + b + c
				for d in tld:
					if not d.startswith('#'):
						outfile.write("www.%s.%s\n" % (hostname, d))
						outfile.write("%s.%s\n" % (hostname, d))

	outfile.close()

def gen2(filename, tld):
	outfile = open(filename, "w")
	for a in string.lowercase:
		for b in string.lowercase:
			hostname = a + b
			for d in tld:
				if not d.startswith('#'):
					outfile.write("www.%s.%s\n" % (hostname, d))
					outfile.write("%s.%s\n" % (hostname, d))
	outfile.close()

def gen1(filename, tld):
	outfile = open(filename, "w")
	for a in string.lowercase:
		hostname = a
		for d in tld:
			if not d.startswith('#'):
				outfile.write("www.%s.%s\n" % (hostname, d))
				outfile.write("%s.%s\n" % (hostname, d))
	outfile.close()

if __name__ == "__main__":
	tldfile = open("../../ptt/databases/tlds.txt")
	tlds = tldfile.readlines()[1:]

	tlds = map(string.strip, tlds)
	print tlds
	gen1("hostnames.tld1", tlds)
	gen2("hostnames.tld2", tlds)
	gen3("hostnames.tld3", tlds)

	isofile = open("../../ptt/databases/iso.txt")
	isos = isofile.readlines()[1:]

	isos = map(string.strip, isos)
	gen1("hostnames.iso1", isos)
	gen2("hostnames.iso2", isos)
	gen3("hostnames.iso3", isos)
