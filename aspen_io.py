"""Configuration script for the http://aspen.io/ website.
"""
import os
import os.path
from pando.configuration import parse
from pando.website import Website

distribution_root = os.path.dirname(__file__)
website = Website( www_root=os.path.join(distribution_root, 'doc')
                 , project_root=os.path.join(distribution_root, 'doc', '.aspen')
                  )
opts = {}

def add_stuff_to_request_context(website, dispatch_result):

    # Define some closures for generating image markup.
    # =================================================

    def translate(src):
        if src[0] != '/':
            rel = os.path.dirname(dispatch_result.match)[len(website.www_root):]
            src = '/'.join([rel, src])
        src = opts['base'] + src
        return src

    def img(src):
        src = translate(src)
        html = '<img src="%s" />' % src
        return html

    def screenshot(short, imgtype='png', href=''):
        """Given foo, go with foo.small.png and foo.png.
        """
        small = img(short + '.small.' + imgtype)
        if not href:
            href = translate(short + '.' + imgtype)
        html = ('<a title="Click for full size" href="%s"'
                'class="screencap">%s</a>')
        return html % (href, small)


    # Make these available within simplates.
    # ======================================

    return {
        'img': img,
        'screenshot': screenshot,
        'translate': translate,
        'version': opts['version'],
        'homepage': False,
        'show_ga': opts['show_ga'],
    }


opts['show_ga'] = parse.yes_no(os.environ.get( 'ASPEN_IO_SHOW_GA'
                                             , 'no'
                                              ).decode('US-ASCII'))
opts['base'] = ''

# this is a dirty nasty hack. We should store the version in the pando module somewhere
opts['version'] = open(os.path.join(website.www_root,'..','version.txt')).read()[:-len('-dev')]

# no idea why this doesn't work
website.renderer_default = 'tornado'
open('/tmp/debugout','a').write('doccnf:' + website.renderer_default + '\n')

website.algorithm.insert_after('dispatch_request_to_filesystem', add_stuff_to_request_context)


if __name__ == '__main__':
    from pando import serve
    serve(website)
