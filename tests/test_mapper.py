import os
import io
import sys
from contextlib import redirect_stdout
import subprocess
import pathlib

# If mapper.py is a script with no functions, simplest is to run it as a subprocess:
def run_mapper(stdin_data, input_file="sample.txt"):
    env = os.environ.copy()
    # Hadoop sets one of these; your script likely reads one
    env.setdefault("mapreduce_map_input_file", f"/path/{input_file}")
    env.setdefault("mapreduce_input_file", f"/path/{input_file}")  # fallback
    p = subprocess.Popen(
        ["python3", "mapper.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    out, err = p.communicate(stdin_data)
    assert p.returncode == 0, f"mapper failed: {err}"
    return out

def test_mapper_counts_lines_per_file():
    data = "a\nb\nc\n"
    out = run_mapper(data, "myfile.txt").strip().splitlines()
    # expect 3 lines => three emissions "myfile.txt\t1"
    assert len(out) == 3
    assert all(line.startswith("myfile.txt\t") for line in out)
    assert set(out) == {"myfile.txt\t1"}
