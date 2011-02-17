Aspen is an async app server for Python.

Releases, docs, support:

    http://aspen.io/


Installation
============

Let's assume you are up on virtualenv. Do this::

    $ mkdir foo
    $ cd foo
    $ virtualenv .aspen
    $ source .aspen/bin/activate
    $ pip install aspen
    $ echo Greetings, program\! > index.html
    $ aspen
    Greetings, program! Welcome to port 8080.


Check http://localhost:8080/ for your new page.


Simplates
=========

Simplates are Aspen's main attraction. Here's what a simplate looks like::

    """This is my simplate.
    """
    import random

    ^L
    n = random.choice(range(10)
    extra_excitement = "!" * n

    ^L
    Greetings, program!{{ extra_excitement }}

Edit index.html with that content, then refresh. You're off and running.

The ^L is an ASCII page break character.

    | Vim | Ctrl-L (in insert mode) |
    | Emacs | C-q C-l |
    | UltraEdit | If I remember right, there is a "Page Break" option on the "Insert" menu. You'd probably remap that. |

Besides learning a weird character, the other kind of wart with simplates is
that you have to keep switching file formats to get the right syntax
highlighting.

    | Vim | :set filetype={python,html,etc} |


