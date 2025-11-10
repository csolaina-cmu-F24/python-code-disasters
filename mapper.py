#!/usr/bin/env python3
# Hadoop Streaming mapper: For each line, emit "<filename>\t1"
import os, sys
fname = os.environ.get("mapreduce_map_input_file") or os.environ.get("map_input_file") or "UNKNOWN"
for _ in sys.stdin:
    sys.stdout.write(f"{fname}\t1\n")
