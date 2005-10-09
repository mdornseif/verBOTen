""" This module implements the class ARCive which allows reading and
writing of archive files like the ones in use at the internet
archive. Beside the archive format versions 1 and 2 which are defined
at http://www.alexa.com/company/arcformat.html ARCive.py implements an
additional version 1003 which stores the documents compressed by zlib
but elsewise is identical to version 2.

TODO: exactly describe version 1003

ARCive can be found at http://c0re.jp/c0de/

 --Maximillian Dornseif

"""

__version__ = '0.1'

__author = 'Maximillian Dornseif'

import re
import time
import md5
import os.path
import zlib, gzip, bz2

defaultcreatorid = 'ARCive.py'
defaultcreatorip = '0.0.0.0'

_version_block1_re = re.compile(r'^filedesc://(?P<path>\S+) (?P<versioninfo>.*) (?P<length>\d+)\n$')
_version_block2_re = re.compile(r'^(?P<versionnumber>\d+) (?P<reserved>.*) (?P<origincode>.+)\n$')
_versioninfo_v1_re = re.compile(r'^(?P<ip>[0-9.]+) (?P<date>\d+) text/plain$')
_versioninfo_v2_re = re.compile(r'^(?P<ip>[0-9.]+) (?P<date>\d+) text/plain 200 - - 0 (?P<filename>\S+)$')
_versioninfo_v1003_re = re.compile(r'^(?P<ip>[0-9.]+) (?P<date>\d+) text/plain 200 - - 0 (?P<filename>\S+)$')

# Used to compare file passed
import types
_STRING_TYPES = (types.StringType,)
if hasattr(types, "UnicodeType"):
    _STRING_TYPES = _STRING_TYPES + (types.UnicodeType,)

def  _fromARCdate(s):
    return time.mktime((int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), -1, -1, 0)) - time.timezone

def  _toARCdate(t):
    return time.strftime('%Y%d%m%H%M%S', time.gmtime(t))


class ARCive:    
    def __init__(self, f, mode="r", creatorid = defaultcreatorid, creatorip = defaultcreatorip):
        """Open the ARC file with mode read 'r', write 'w' or append 'a'.

        Mode can also contain the desired ARCive version if creating a
        new file. Only '2' and '1003' ars supported. 'w1003' will
        create a Version 1003 ARCive. If you obmit version, version 2
        is assumed. If file is not an filename it can also be an open
        file-object.  You can also set the 'creatorid' and the
        'creatorip' which are only relevant when writing to an arcive. 

        If f ends in bz2 or gz we do the right thing by
        by transparently compressing/decompressing the data.
        """
        
        # code partly taken from zipfile.py
        self.mode = key = mode[0]
        self.creatorid = creatorid
        self.creatorip = creatorip
        self.debug = 0
        self.size = 0

        if key == 'w':
            if len(mode) == 1:
                self.version = 2
            else:
                self.version = int(mode[1:])
                mode = mode[0]

        # Check if we were passed a file-like object
        if type(f) in _STRING_TYPES:
            self.filename = f
            modeDict = {'r' : 'rb', 'w': 'wb', 'a' : 'r+b'}
            if f.endswith('.bz2'):
                self.fd = bz2.BZ2File(f, modeDict[mode[0]])
            elif f.endswith('.gz'):
                self.fd = gzip.GzipFile(f, modeDict[mode[0]])
            else:
              self.fd = open(f, modeDict[mode[0]])
        else:
            self.fd = f
            self.filename = getattr(f, 'name', None)

        if key == 'r':
            self._read_version_block()
            self.size = os.path.getsize(self.filename)
        elif key == 'w':
            # write a 'dummy' header
            if self.version == 2:
                self._write_headerv2()
            elif self.version == 1003:
                self._write_headerv1003()
            else:
                raise RuntimeError, 'Unknown ARCive Version'
        elif key == 'a':
            raise NotImplementedError
        else:
            raise RuntimeError, 'Mode must be "r", "w" or "a"'


    def _parse_version_block1(self):
        """Parse versioninfo for v1"""
        m = _versioninfo_v1_re.match(self.versioninfo)
        if m == None:
            raise RuntimeError, "Not a valid v1 versioninfo header: %r" % self.versioninfo
        self.creatorip = m.group('ip')
        self.creationdate = m.group('date')
        self.urlrecord_re = re.compile(r'^(?P<url>.+) (?P<archiverip>[0-9.]+) (?P<date>\d+) (?P<contenttype>\S+|\S+;\s+\S+) (?P<length>\d+)\n$') 


    def _parse_version_block2(self):
        """Parse versioninfo for v2"""
        m = _versioninfo_v2_re.match(self.versioninfo)
        if m == None:
            raise RuntimeError, "Not a valid v2 versioninfo header: %r" % self.versioninfo
        self.creatorip = m.group('ip')
        self.creationdate = m.group('date')
        self.creatorfilenmame = m.group('filename') 
        self.urlrecord_re = re.compile(r'^(?P<url>.+) (?P<archiverip>[0-9.]+) (?P<date>\d+) (?P<contenttype>\S+|\S+;\s+\S+) (?P<resultcode>\d+) (?P<checksum>.+) (?P<location>.+) (?P<offset>\d+) (?P<filename>.+) (?P<length>\d+)\n$') 

    def _parse_version_block1003(self):
        """Parse versioninfo for v1003"""
        m = _versioninfo_v1003_re.match(self.versioninfo)
        if m == None:
            raise RuntimeError, "Not a valid v1003 versioninfo header: %r" % self.versioninfo
        self.creatorip = m.group('ip')
        self.creationdate = m.group('date')
        self.creatorfilenmame = m.group('filename') 
        self.urlrecord_re = re.compile(r'^(?P<url>.+) (?P<archiverip>[0-9.]+) (?P<date>\d+) (?P<contenttype>\S+|\S+;\s+\S+?) (?P<resultcode>\d+) (?P<checksum>.+) (?P<location>.+) (?P<offset>\d+) (?P<filename>.+) (?P<length>\d+)\n$') 

    def _read_version_block(self):
        l = self.fd.readline()
        m = _version_block1_re.match(l)
        if m == None:
            raise RuntimeError, "Not a valid arc file header line 1: %r" % (l)
        self.path = m.group('path')
        self.versioninfo = m.group('versioninfo')
        self.path = m.group('length')
        l = self.fd.readline()
        m = _version_block2_re.match(l)
        if m == None:
            raise RuntimeError, "Not a valid arc file header line 2: %r" % (l)
        self.version = int(m.group('versionnumber'))
        self.reserved = m.group('reserved')
        self.origincode = m.group('origincode')
        l = self.fd.readline()
        self.recorddefinition = l.strip()
        if self.version == 1:
            self._parse_version_block1()
        elif self.version == 2:
            self._parse_version_block2()
        elif self.version == 1003:
            self._parse_version_block1003()
        else:
            raise RuntimeError, "unknown arc version: %d" % self.version


    def _write_headerv2(self):
        """Write a ARCive header v2"""

        headerrest = "2 0 %s\nURL IP-address Archive-date Content-type Result-code Checksum Location Offset Filename Archive-length\n" % (self.creatorid)
        self.fd.write("filedesc://%s %s %s text/plain 200 - - 0 %s %d\n%s"  % (os.path.join('', self.filename), self.creatorip, _toARCdate(time.time()), self.filename, len(headerrest), headerrest))


    def _write_headerv1003(self):
        """Write a ARCive header v1003"""
        
        headerrest = "1003 0 %s\nURL IP-address Archive-date Content-type Result-code Checksum Location Offset Filename Archive-length\n" % (self.creatorid)
        self.fd.write("filedesc://%s %s %s text/plain 200 - - 0 %s %d\n%s"  % (os.path.join('', self.filename), self.creatorip, _toARCdate(time.time()), self.filename, len(headerrest), headerrest))


    def close(self):
        """Close ARCive."""
        
        self.fd.close()

    def getDir(self):
        """Return a dictionary representing the contents of the ARCive.

        The keys of the dictionary are the urls. The entries are a
        list of tuples containing (time, offset). 'time' denotes the
        time this record was saved to the ARCive and 'offset' the
        position relative to the beginning of the file where the
        record can be found.

        This means a url can be present more than once in an ARCive if
        the data is insered at different times.
        """

        oldpos = self.fd.tell()
        self.fd.seek(0)
        self._read_version_block()
        self.dir = {}
        while 1:
            # this could be much faster by refraining from reading th body
            x = self.readRawDoc(donotdecompress=1)
            if x == None:
                break
            meta = x[0]
            if meta['url'] not in self.dir:
                self.dir[meta['url']] = []
            if self.debug:
                print meta
            self.dir[meta['url']].append({"date": meta['date'],
                                          "offset": meta['offset'],
                                          "checksum": int(meta['checksum'], 16)})
        # reset file pointer
        self.fd.seek(oldpos)
        return self.dir


    def writeRawDoc(self, data, url, mimetype = 'application/octet-stream', result = 200,
                    location = '-', timestamp=None):
        """Write new data to the ARCive.

        'data' must be data returned by http containing headers. 'url'
        must describe the location where the data was
        retrived. 'mimetype' can set the type of the data written. If
        mimetype is not set, it defaults to
        'application/octet-stream'. 'result' is the integer http
        result code. 'location' can be set to the location to where
        the client was redirected when trying to access url."""

        if not timestamp:
            timestamp = time.time()
        hash = md5.new(data).hexdigest()
        pos = str(self.fd.tell())
        # only in ARCive version 1003 data is compressed using zlib
        if self.version == 1003:
            data = zlib.compress(data)
        self.fd.write("\n%s %s %s %s %d %s %s %s %s %s\n" % (url, self.creatorip,
                                                             _toARCdate(timestamp), mimetype,
                                                             result, hash, location, pos,
                                                             self.filename, len(data)))
        self.fd.write(data)
        #self.fd.flush()
        self.size = self.fd.tell()

    def readRawDoc(self, donotdecompress = None):
        """Read the next document from the current position.

        It will return a tuple (meta, data) where 'meta' is a
        dictionary containing information about the document. The
        only entrys in this dictionary you can rely on are 'length' and
        'date'.

        if the file has ended ({}, None is returned).

        If donotdecompress is true compressed data will returned to
        the caller in compressed form."""

        l = self.fd.readline()
        if l == '':
          return {}, None
        if l != '\n':
            raise RuntimeError, 'invalid doc header line 1: %r' % l 
        l = self.fd.readline()
        m = self.urlrecord_re.match(l)
        if m == None:
            raise RuntimeError, "Not a valid arc doc header line 2: %r" % l 
        meta = m.groupdict()
        meta['length'] = int(m.group('length'))
        meta['offset'] = int(m.group('offset'))
        meta['date'] = _fromARCdate(m.group('date'))
        data = self.fd.read(meta['length'])
        # only in ARCive version 1003 data is decompressed using zlib
        if self.version == 1003 and not donotdecompress:
            data = zlib.decompress(data)
            meta['complength'] = meta['length'] 
            meta['length'] = len(data)
        return(meta, data)

    def readRawDocAtPos(self, pos, donotdecompress = None):
        self.fd.seek(pos)
        return self.readRawDoc(donotdecompress)
        
if __name__ == '__main__':
    # very simple self-test

    print "create a new archive called 'testN.arc' and write some data into it"
    a = ARCive('testN.arc', 'w1003')
    a.writeRawDoc('a test data 1 X', 'http://url1/X')
    a.writeRawDoc('b test data 2 X', 'http://url2/X')
    a.writeRawDoc('c test data 3 X', 'http://url3/X')
    a.close()

    print "reopen it and print its contents"
    a = ARCive('testN.arc', 'r')
    from pprint import pprint
    pprint(a.getDir())
    
