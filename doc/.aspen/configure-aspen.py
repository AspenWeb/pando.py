import os

from aspen.configuration import parse
from aspen_io import opts, inbound


opts['show_ga'] = parse.yes_no(os.environ.get( 'ASPEN_IO_SHOW_GA'
                                             , 'no'
                                              ).decode('US-ASCII'))
opts['base'] = ''
opts['version'] = open('../version.txt').read()[:-len('-dev')]


website.hooks.inbound_early = [inbound]
