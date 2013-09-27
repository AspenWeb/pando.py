#!/usr/bin/env python
"""Benchmark assert

without assert: 0.79 seconds
with assert: 0.95 seconds

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time

if __name__ == '__main__':
    start = time.time()

    for i in range(10000000):
        #pass
        assert 1 == 1

    end = time.time()
    print("%5.2f" % (end - start))
