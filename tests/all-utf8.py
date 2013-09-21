#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

for i in range(2**16):
    u = unichr(i).encode('utf8')
    sys.stdout.write("%5d %s  " % (i, u))
    if i % 6 == 0:
        print

