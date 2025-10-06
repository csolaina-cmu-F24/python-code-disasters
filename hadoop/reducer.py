#!/usr/bin/env python3
import sys

current = None
acc = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    k, v = line.split('\t', 1)
    v = int(v)
    if current is None:
        current = k
    if k != current:
        print(f'"{current}": {acc}')
        current = k
        acc = 0
    acc += v

if current is not None:
    print(f'"{current}": {acc}')
