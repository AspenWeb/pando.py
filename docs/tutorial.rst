##########
 Tutorial
##########

*************
 Quick Start
*************

Given: `POSIX <http://en.wikipedia.org/wiki/POSIX#POSIX-oriented_operating_systems>`_
and `virtualenv <http://pypi.python.org/pypi/virtualenv>`_

Step 1: Make a sandbox::

    $ virtualenv foo
    $ cd foo
    $ . bin/activate

Step 2: Install `pando from PyPI <http://pypi.python.org/pypi/pando>`_::

    (foo)$ pip install pando
    blah
    blah
    blah

Step 3: Create a website root::

    (foo)$ mkdir www
    (foo)$ cd www

Step 4: Create a web page, and start pando inside it::

    (foo)$ echo Greetings, program! > index.html.spt
    (foo)$ python -m pando
    Greetings, program! Welcome to port 8080.

Step 5: Check `localhost <http://localhost:8080>`_ for your new page!

    .. image:: images/greetings-program.png
