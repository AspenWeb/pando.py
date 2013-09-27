#!/usr/bin/env python
"""Benchmark try vs. except

without raise Exception: 0.94 seconds
with raise Exception: 9.26 seconds

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time

if __name__ == '__main__':
    start = time.time()

    for i in range(10000000):
        try:
            raise Exception
            pass
        except Exception:
            pass

    end = time.time()
    print("%5.2f" % (end - start))
