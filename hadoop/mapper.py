#!/usr/bin/env python3
import os, sys

# Hadoop Streaming exposes input filename via one of these env vars depending on version
fname = os.environ.get('mapreduce_map_input_file') or os.environ.get('map_input_file') or 'UNKNOWN'

for _ in sys.stdin:
    # emit 1 per line to count lines per file
    print(f"{fname}\t1")
