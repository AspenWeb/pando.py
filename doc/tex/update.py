#!/usr/bin/env python

import os
import stat
import subprocess
import time

c = 'make'
mtimes = {}
try:
    while 1:
        made = False
        for name in os.listdir('.'):
            if not (  name == 'Makefile'
                   or name.endswith('.tex')
                   or name.endswith('.css')
                     ):
                continue
            if name not in mtimes:
                mtime = 0
            else:
                mtime = mtimes[name]
            newtime = os.stat(name)[stat.ST_MTIME]
            if mtime != newtime:
                mtimes[name] = newtime
                if not made:
                    p = subprocess.Popen(c, shell=True)
                    sts = os.waitpid(p.pid, 0)
                    made = True
                t = time.strftime('%I:%M.%S%p').replace(' 0', ' ')
                print "%s @ %s" % (name, t)
        time.sleep(0.5)
except KeyboardInterrupt:
    os.system("make clean")
