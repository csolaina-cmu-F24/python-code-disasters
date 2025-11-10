#!/usr/bin/env python3
# Hadoop Streaming reducer: sum counts per filename
import sys
cur_key, cur_sum = None, 0
for line in sys.stdin:
    key, _ = line.rstrip("\n").split("\t", 1)
    if key != cur_key and cur_key is not None:
        print(f"{cur_key}\t{cur_sum}")
        cur_sum = 0
    cur_key = key
    cur_sum += 1
if cur_key is not None:
    print(f"{cur_key}\t{cur_sum}")
