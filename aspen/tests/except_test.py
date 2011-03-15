#!/usr/bin/env python
"""Benchmark try vs. except

without raise Exception: 0.94 seconds
with raise Exception: 9.26 seconds

"""
import time

start = time.time()

for i in range(10000000):
    try:
        raise Exception
        pass
    except Exception:
        pass

end = time.time()
print "%5.2f" % (end - start)
