#!/usr/bin/env python3
import os, sys

# Hadoop Streaming exposes the current input file path via an env var.
# Try modern then legacy names:
path = os.environ.get("mapreduce_map_input_file") or os.environ.get("map_input_file") or ""
fname = os.path.basename(path) or "UNKNOWN"

quoted = f"\"{fname}\""  # e.g., "myfile.py"
for _ in sys.stdin:
    # one count per input line
    print(f"{quoted}\t1")
