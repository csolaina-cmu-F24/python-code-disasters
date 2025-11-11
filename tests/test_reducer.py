import subprocess

def run_reducer(stdin_data):
    p = subprocess.Popen(
        ["python3", "reducer.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate(stdin_data)
    assert p.returncode == 0, f"reducer failed: {err}"
    return out

def test_reducer_sums_by_key():
    input_pairs = "\n".join([
        "fileA.txt\t1",
        "fileA.txt\t1",
        "fileB.txt\t1",
        "fileA.txt\t1",
    ]) + "\n"
    out = run_reducer(input_pairs).strip().splitlines()
    # expect:
    # "fileA.txt\t3"
    # "fileB.txt\t1"
    d = dict(line.split("\t", 1) for line in out)
    assert d["fileA.txt"] == "3"
    assert d["fileB.txt"] == "1"
