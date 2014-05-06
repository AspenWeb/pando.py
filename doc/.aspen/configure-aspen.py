import os

from aspen.configuration import parse
from aspen_io import opts, add_stuff_to_request_context

os.chdir(website.www_root)

opts['show_ga'] = parse.yes_no(os.environ.get( 'ASPEN_IO_SHOW_GA'
                                             , 'no'
                                              ).decode('US-ASCII'))
opts['base'] = ''
opts['version'] = open('../version.txt').read()[:-len('-dev')]

# no idea why this doesn't work
website.renderer_default = 'tornado'
open('/tmp/debugout','a').write('doccnf:' + website.renderer_default + '\n')

website.algorithm.insert_after('parse_environ_into_request', add_stuff_to_request_context)
