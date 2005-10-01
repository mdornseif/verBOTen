#!/usr/bin/python

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
# vi:ts=4:et
# $Id$

#
# Usage: python retriever-multi.py <file with URLs to fetch> [<# of
#          concurrent connections>]
#

num_conn = 30

import sys, time, random
import ARCive
import pycurl

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass

# Make a queue with (url, filename) tuples
queue = []
for url in open('hosts'):
    url = url.strip()
    if not url or url[0] == "#":
        continue
    queue.append(url)
random.shuffle(queue)

# Check args
assert queue, "no URLs given"

archivename = 'robots-%d.arc' % time.time()
archive = ARCive.ARCive(archivename, 'w')

num_urls = len(queue)
num_conn = min(num_conn, num_urls)
assert 1 <= num_conn <= 10000, "invalid number of concurrent connections"
print "PycURL %s (compiled against 0x%x)" % (pycurl.version, pycurl.COMPILE_LIBCURL_VERSION_NUM)
print "----- Getting", num_urls, "URLs into", archivename, "using", num_conn, "connections -----"
startt = time.time()


# Pre-allocate a list of curl objects
m = pycurl.CurlMulti()
m.handles = []
for i in range(num_conn):
    c = pycurl.Curl()
    c.body = StringIO()
    c.setopt(pycurl.WRITEFUNCTION, c.body.write)
    c.setopt(pycurl.HEADER, 1)
    c.setopt(pycurl.FOLLOWLOCATION, 0)
    c.setopt(pycurl.CONNECTTIMEOUT, 30)
    #c.setopt(pycurl.DNS_CACHE_TIMEOUT, -1)
    c.setopt(pycurl.TIMEOUT, 120)
    c.setopt(pycurl.NOSIGNAL, 1)
    # c.setopt(pycurl.VERBOSE, 1)
    m.handles.append(c)
    
# Main loop
freelist = m.handles[:]
num_processed = 0
while queue:
    # If there is an url to process and a free curl object, add to multi stack
    while queue and freelist:
        hostname = queue.pop(0)
        c = freelist.pop()
        c.url = 'http://%s/robots.txt' % hostname
        c.setopt(pycurl.URL, c.url)
        m.add_handle(c)
    # Run the internal curl state machine for the multi stack
    while 1:
        ret, num_handles = m.perform()
        if ret != pycurl.E_CALL_MULTI_PERFORM:
            break
    # Check for curl objects which have terminated, and add them to the freelist
    while 1:
        num_q, ok_list, err_list = m.info_read()
        for c in ok_list:
            m.remove_handle(c)
            print "Success:", c.getinfo(pycurl.RESPONSE_CODE), c.getinfo(pycurl.EFFECTIVE_URL)
            if c.getinfo(pycurl.RESPONSE_CODE) == 200:
              # avoid html
              if 'tml>' not in c.body.getvalue() and 'TML>' not in c.body.getvalue():
                archive.writeRawDoc(c.body.getvalue(), c.url, mimetype = c.getinfo(pycurl.CONTENT_TYPE))
            c.body.seek(0)
            c.body.truncate()
            freelist.append(c)
        for c, errno, errmsg in err_list:
            m.remove_handle(c)
            print "Failed: ", c.url, errno, errmsg
            freelist.append(c)
        num_processed = num_processed + len(ok_list) + len(err_list)
        if num_q == 0:
            break
    # Currently no more I/O is pending, could do something in the meantime
    # (display a progress bar, etc.).
    # We just call select() to sleep until some more data is available.
    m.select(3.0)


archive.close()
# Cleanup
for c in m.handles:
    c.close()
m.close()

endt = time.time()
deltat = endt - startt
print "processed %d urls in %.2f seconds (%.4f urls/s)" % (num_urls, deltat, (num_urls / deltat))

import sys
import robotparser
import threading
import time

