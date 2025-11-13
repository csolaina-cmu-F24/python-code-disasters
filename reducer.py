#!/usr/bin/env python3
import sys

current = None
total = 0

def flush(key, val):
    if key is not None:
        # Exact required format: “File name”: # of lines
        print(f"{key}: {val}")

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    key, _, val = line.partition("\t")
    try:
        n = int(val)
    except ValueError:
        continue
    if key != current:
        flush(current, total)
        current, total = key, n
    else:
        total += n

flush(current, total)
