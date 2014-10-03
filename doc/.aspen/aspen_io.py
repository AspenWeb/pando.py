"""Helpers for the http://aspen.io/ website.
"""
from os.path import dirname


opts = {} # populate this in configure-aspen.py


def add_stuff_to_request_context(website, request, dispatch_result):

    # Define some closures for generating image markup.
    # =================================================

    def translate(src):
        if src[0] != '/':
            rel = dirname(dispatch_result.match)[len(website.www_root):]
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

    request.context['img'] = img
    request.context['screenshot'] = screenshot
    request.context['translate'] = translate
    request.context['version'] = opts['version']
    request.context['homepage'] = False
    request.context['show_ga'] = opts['show_ga']
