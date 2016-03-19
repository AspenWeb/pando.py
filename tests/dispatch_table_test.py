#!/usr/bin/python

import os.path
import posixpath
import pytest
from pando.testing.harness import Harness

tablefile = os.path.join(os.path.dirname(__file__), 'dispatch_table_data.rst')

def find_cols(defline, header_char='='):
    """
    return a sorted list of (start, end) indexes into defline that
    are the beginning and ending indexes of column definitions
    based on a reStructuredText table header line.
    Note that this is a braindead simple version that only understands
    header_chars and spaces (no other whitespace)
    """
    i = 0;
    colstarts = []
    colends = []
    while i < len(defline):
        if len(colstarts) <= len(colends):
            nextstart = defline.find(header_char, i)
            if nextstart >= 0:
                colstarts.append(nextstart)
                i = nextstart
            else:
                break
        else:
            nextend = defline.find(' ',i)
            if nextend >= 0:
                colends.append(nextend)
                i = nextend
            else:
                colends.append(len(defline))
                break

    return zip(colstarts,colends)

def fields_from(dataline, cols):
    """
    Given a data line and a set of column definitions,
    strip the data and return it as a list
    """
    fields = []
    for start, fin in cols:
        fields.append(dataline[start:fin].strip())
    return fields

def get_table_entries():
    table = open(tablefile,'r').readlines()

    tabledefline = table[0].strip()
    cols = find_cols(tabledefline)

    headers = fields_from(table[1], cols)
    inputfiles = headers[:headers.index('/')]
    requests = headers[headers.index('/'):]

    # We 'know' that table[0] == table[2], both header deflines, so skip down
    results = []
    for line in table[3:]:
        if line.strip() == tabledefline: break # found ending header, ignore the rest
        if line.strip().startswith('#'): continue # skip comment lines
        fields = fields_from(line, cols)
        files = [ x for i, x in enumerate(inputfiles) if fields[i] == 'X' ]
        expected = fields[len(inputfiles):]
        results += [ (files, r, expected[i]) for i, r in enumerate(requests) ]
    return results

def format_result(request, dispatch_result=None, **ignored):
    """
    turn a raw request result into a string compatible with the table-driven test
    """
    wilds = request.line.uri.path
    wildtext = ",".join("%s='%s'" % (k, wilds[k]) for k in sorted(wilds))
    result = dispatch_result.match if dispatch_result else ''
    if wildtext: result += " (%s)" % wildtext
    return result

GENERIC_SPT = """
[-----]
[-----] text/plain
Greetings, Program!
"""

@pytest.mark.parametrize("files,request_uri,expected", get_table_entries())
def test_all_table_entries(harness, files, request_uri, expected):
    # set up the specified files
    realfiles = tuple([ f if f.endswith('/') else (f, GENERIC_SPT) for f in files ])
    harness.fs.www.mk(*realfiles)
    # make the request and get the response code and the request object (sadly we can't get both with one request)
    response = harness.simple(uripath=request_uri, filepath=None, want='response', raise_immediately=False)
    result = unicode(response.code)
    if result == '200':
        state = harness.simple( uripath=request_uri
                              , filepath=None
                              , want='state'
                              , raise_immediately=False
                               )
        path = format_result(**state)
        if os.sep != posixpath.sep:
            path = path.replace(os.sep, posixpath.sep)
        path = path[len(harness.fs.www.root)+1:]
        if path:
            result += " " + path
    elif result == '302':
        result += ' ' + response.headers['Location']
    if expected.endswith("*"):
        expected = expected[:-1]
    assert result == expected, "Requesting %r, got %r instead of %r" % (request_uri, result, expected)


if __name__ == '__main__':
    # output the table with answers the current dispatcher gives
    # currently this has to be run manually with:
    #    ./env/bin/python tests/dispatch_table_test | grep -v ^pid
    table = open(tablefile,'r').readlines()

    tabledefline = table[0].strip()
    cols = find_cols(tabledefline)

    headers = fields_from(table[1], cols)
    answercol = headers.index('/')
    inputfiles = headers[:answercol]
    requests = headers[answercol:]


    for line in table[:3]:
        print(line)
    # We 'know' that table[0] == table[2], both header deflines, so skip down
    for line in table[3:]:
        if line.strip() == tabledefline: break # found ending header, ignore the rest
        if line.strip().startswith('#'): continue # skip comment lines
        fields = fields_from(line, cols)
        files = [ x for i, x in enumerate(inputfiles) if fields[i] == 'X' ]
        expected = fields[len(inputfiles):]
        resultcolstart = cols[answercol][0]
        resultline = line[:resultcolstart] # input files
        harness = Harness()
        realfiles = tuple([ f if f.endswith('/') else (f, GENERIC_SPT) for f in files ])
        harness.fs.www.mk(*realfiles)
        for i,request_uri in enumerate(requests):
            result = unicode(harness.simple(uripath=request_uri, filepath=None, want='response.code', raise_immediately=False))
            if result not in [ '404' ]:
                state = harness.simple( uripath=request_uri
                                      , filepath=None
                                      , want='state'
                                      , raise_immediately=False
                                       )
                path = format_result(**state)
                path = path[len(harness.fs.www.root)+1:]
                if path:
                    result += " " + path
            col = answercol + i
            resultline += result + (' ' * (cols[col][1] - cols[col][0] - len(result)))
            if col < len(cols) - 1:
                resultline += ' ' * (cols[col+1][0] - cols[col][1])
        print(resultline)



