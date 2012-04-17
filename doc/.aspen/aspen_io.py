"""Helpers for the http://aspen.io/ website.

This is where we implement serving images from a CDN in production. All files
must use the img and screenshot helpers defined herein to participate in this
system.

"""
from os.path import dirname


opts = {} # populate this in configure-aspen.py


def inbound(request):

    # Define some closures for generating image markup.
    # =================================================

    def translate(src):
        if src[0] != '/':
            rel = dirname(request.fs)[len(request.root):]
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


# TODO Redirect direct requests to the CDN.
# TODO What about css/js files?
# TODO What about images in css?
