#!/usr/bin/env python
"""Benchmark assert

without assert: 0.79 seconds
with assert: 0.95 seconds

"""
import time

start = time.time()

for i in range(10000000):
    #pass
    assert 1 == 1

end = time.time()
print "%5.2f" % (end - start)
