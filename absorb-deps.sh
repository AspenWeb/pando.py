#!/bin/sh

TOP="`dirname $(readlink -f $0)`"

CHERRYPY_DL_BASE="http://download.cherrypy.org/cherrypy"
CHERRYPY_VERSION="3.2.2"
CHERRYPY_DIR="CherryPy-$CHERRYPY_VERSION"
CHERRYPY_TARBALL="$CHERRYPY_DIR.tar.gz"
CHERRYPY_URL="$CHERRYPY_DL_BASE/$CHERRYPY_VERSION/$CHERRYPY_TARBALL"

TORNADO_DL_BASE="http://github.com/downloads/facebook/tornado"
TORNADO_VERSION="2.3"
TORNADO_DIR="tornado-$TORNADO_VERSION"
TORNADO_TARBALL="$TORNADO_DIR.tar.gz"
TORNADO_URL="$TORNADO_DL_BASE/$TORNADO_TARBALL"

MIMEPARSE_DL_BASE="http://pypi.python.org/packages/source/m/mimeparse"
MIMEPARSE_VERSION="0.1.3"
MIMEPARSE_DIR="mimeparse-$MIMEPARSE_VERSION"
MIMEPARSE_TARBALL="mimeparse-$MIMEPARSE_VERSION.tar.gz"
MIMEPARSE_URL="$MIMEPARSE_DL_BASE/$MIMEPARSE_TARBALL"


mkdir -p "$TOP/downloads"
cd "$TOP/downloads"


if [ ! -d "$CHERRYPY_DIR" ] ; then
    curl -O -L "$CHERRYPY_URL"
    tar -xvzf "$CHERRYPY_TARBALL"
fi
rm -rvf "$TOP/aspen/_cherrypy"
mkdir -p "$TOP/aspen/_cherrypy"
rsync -av "$CHERRYPY_DIR/cherrypy/wsgiserver" "$TOP/aspen/_cherrypy/"


if [ ! -d "$TORNADO_DIR" ] ; then
    curl -O -L "$TORNADO_URL"
    tar -xzvf "$TORNADO_TARBALL"
fi
for f in escape.py template.py ; do
    cp -v "$TORNADO_DIR/tornado/$f" "$TOP/aspen/_tornado/$f"
done


if [ ! -d "$MIMEPARSE_DIR" ] ; then
    curl -O -L "$MIMEPARSE_URL"
    tar -xzvf "$MIMEPARSE_TARBALL"
fi
cp -v "$MIMEPARSE_DIR/mimeparse.py" "$TOP/aspen/_mimeparse/mimeparse.py"
