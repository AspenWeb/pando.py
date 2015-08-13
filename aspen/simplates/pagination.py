"""
aspen.resources.pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re


SPLITTER = '^\[---+\](?P<header>.*?)(\n|$)'
ESCAPED_SPLITTER = '^\\\\(\\\\*)(\[---+\].*?(\n|$))'
SPECLINE_SPLIT = '(?:\s+|^)via\s+'

SPLITTER = re.compile(SPLITTER, re.MULTILINE)
ESCAPED_SPLITTER = re.compile(ESCAPED_SPLITTER, re.MULTILINE)
SPECLINE_SPLIT = re.compile(SPECLINE_SPLIT)


class Page(object):
    __slots__ = ('header', 'content', 'offset')

    def __init__(self, content, header='', offset=0):
        self.content = content
        self.header = header.decode('ascii')
        self.offset = offset

    @property
    def padded_content(self):
        return ('\n' * self.offset) + self.content


def split(raw):
    '''Pure split generator. This function defines the plain logic to split a
    string into a list of pages
    '''

    current_index = 0
    line_offset = 0
    header = ''

    for page_break in SPLITTER.finditer(raw):
        content = raw[current_index:page_break.start()]
        yield Page(content, header, line_offset)
        line_offset += content.count('\n') + 1
        header = page_break.group('header').strip()
        current_index = page_break.end()

    # Yield final page. If no page dividers were found, this will be all of it
    content = raw[current_index:]
    yield Page(content, header, line_offset)

def escape(content):
    '''Pure escape method. This function defines the logic to properly convert
    escaped splitter patterns in a string
    '''
    return ESCAPED_SPLITTER.sub(r'\1\2', content)

def split_and_escape(raw):
    '''This function defines the logic to split and escape a string.
    '''
    for page in split(raw):
        page.content = escape(page.content)
        yield page

def parse_specline(header):
    '''Attempt to parse the header in a page returned from split(...) as a
    specline. Returns a tuple (content_type, renderer)
    '''
    parts = SPECLINE_SPLIT.split(header, 1) + ['']
    return parts[0].strip(), parts[1].strip()

def can_split(raw, splitter=SPLITTER):
    '''Determine if a text block would be split by a splitter
    '''
    return bool(SPLITTER.search(raw))

