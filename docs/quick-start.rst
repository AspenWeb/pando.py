

Quick Start
===========

Given: `POSIX <http://en.wikipedia.org/wiki/POSIX#POSIX-oriented_operating_systems>`_
and `virtualenv <http://pypi.python.org/pypi/virtualenv>`_

Step 1: Make a sandbox:

    $ virtualenv foo
    $ cd foo
    $ . bin/activate</pre>
    ::

Step 2: Install `aspen from PyPI <http://pypi.python.org/pypi/aspen>`_:

    (foo)$ pip install aspen
    blah
    blah
    blah
    ::

Step 3: Create a website root:

    (foo)$ mkdir www
    (foo)$ cd www</pre>
    ::

Step 4: Create a web page, and start aspen inside it:

    (foo)$ echo Greetings, program! > index.html.spt
    (foo)$ aspen
    Greetings, program! Welcome to port 8080.
    ::

Step 5: Check `localhost http://localhost:8080`_ for your new page!

    .. image:: greetings-program.png

{% end %}
