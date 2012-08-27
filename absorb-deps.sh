#!/bin/sh

# This script should be maybe both a development-time and release-time
# dependency?  I think the goal is to have the *aspen* source tree free of code
# that doesn't belong to aspen while still allowing us to ship vendorized
# libraries (batteries!)

TOP="`python -S -c "
import os, sys
sys.stdout.write(os.path.dirname(os.path.abspath('$0')))
"`"
cd "$TOP"
eval "`cat "$TOP/deps.txt" | tr '[:lower:]' '[:upper:]' | sed 's/ /_VERSION=/'`"

CHERRYPY_DL_BASE="http://download.cherrypy.org/cherrypy"
CHERRYPY_DIR="CherryPy-$CHERRYPY_VERSION"
CHERRYPY_TARBALL="$CHERRYPY_DIR.tar.gz"
CHERRYPY_URL="$CHERRYPY_DL_BASE/$CHERRYPY_VERSION/$CHERRYPY_TARBALL"

TORNADO_DL_BASE="http://github.com/downloads/facebook/tornado"
TORNADO_DIR="tornado-$TORNADO_VERSION"
TORNADO_TARBALL="$TORNADO_DIR.tar.gz"
TORNADO_URL="$TORNADO_DL_BASE/$TORNADO_TARBALL"

MIMEPARSE_DL_BASE="http://pypi.python.org/packages/source/m/mimeparse"
MIMEPARSE_DIR="mimeparse-$MIMEPARSE_VERSION"
MIMEPARSE_TARBALL="mimeparse-$MIMEPARSE_VERSION.tar.gz"
MIMEPARSE_URL="$MIMEPARSE_DL_BASE/$MIMEPARSE_TARBALL"


maybe_untar_url_to_dir() {
    if [ ! -d "$2" ] ; then
        curl -O -L "$1"
        tar -xvzf "`basename $1`"
    fi
}

redo_tree() {
    rm -rvf "$1"
    mkdir -p "$1"
    touch "$1/__init__.py"
}

set -e
set -x


mkdir -p "$TOP/downloads"
cd "$TOP/downloads"


maybe_untar_url_to_dir "$CHERRYPY_URL" "$CHERRYPY_DIR"
redo_tree "$TOP/aspen/_cherrypy"
rsync -av "$CHERRYPY_DIR/cherrypy/wsgiserver" "$TOP/aspen/_cherrypy/"


maybe_untar_url_to_dir "$TORNADO_URL" "$TORNADO_DIR"
redo_tree "$TOP/aspen/_tornado"
for f in escape.py template.py ; do
    cp -v "$TORNADO_DIR/tornado/$f" "$TOP/aspen/_tornado/$f"
done


maybe_untar_url_to_dir "$MIMEPARSE_URL" "$MIMEPARSE_DIR"
redo_tree "$TOP/aspen/_mimeparse"
cp -v "$MIMEPARSE_DIR/mimeparse.py" "$TOP/aspen/_mimeparse/mimeparse.py"
