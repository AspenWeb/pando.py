import os
import os.path
from aspen.configuration import parse
from aspen_io import opts, add_stuff_to_request_context

opts['show_ga'] = parse.yes_no(os.environ.get( 'ASPEN_IO_SHOW_GA'
                                             , 'no'
                                              ).decode('US-ASCII'))
opts['base'] = ''

# this is a dirty nasty hack. We should store the version in the aspen module somewhere
opts['version'] = open(os.path.join(website.www_root,'..','version.txt')).read()[:-len('-dev')]

# no idea why this doesn't work
website.renderer_default = 'tornado'
open('/tmp/debugout','a').write('doccnf:' + website.renderer_default + '\n')

website.algorithm.insert_after('dispatch_request_to_filesystem', add_stuff_to_request_context)
