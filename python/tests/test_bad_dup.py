import importlib.util
import pathlib
import runpy
import sys


# --- dynamic import of repo/python/bad-dup.py as module "bad_dup" ---
MODULE_PATH = pathlib.Path(__file__).resolve().parent.parent / "bad-dup.py"
assert MODULE_PATH.exists(), f"Could not find file: {MODULE_PATH}"

spec = importlib.util.spec_from_file_location("bad_dup", MODULE_PATH)
bad_dup = importlib.util.module_from_spec(spec)
sys.modules["bad_dup"] = bad_dup
spec.loader.exec_module(bad_dup)


def test_summarize_regular(capsys):
    summary = bad_dup.summarize(bad_dup.DUMMY_DATA, "Report X")
    out = capsys.readouterr().out
    assert "Report X:" in out
    assert summary["title"] == "Report X"
    assert summary["avg"] == 42
    assert summary["count"] == 3
    assert summary["names"] == "alpha,beta,gamma"


def test_summarize_empty(capsys):
    summary = bad_dup.summarize([], "Empty")
    out = capsys.readouterr().out
    assert "Empty:" in out
    assert summary["avg"] == 0
    assert summary["count"] == 0
    assert summary["names"] == ""


def test_pipeline_run_happy_path(capsys):
    res = bad_dup.pipeline_run(bad_dup.DUMMY_DATA, "pipeline_run_a")
    out = capsys.readouterr().out
    assert "pipeline_run_a: start" in out
    assert "pipeline_run_a: total" in out
    # 3 items -> cleaned: 3 rows -> parts [84, 42], total 126
    assert res["parts"] == [84, 42]
    assert res["total"] == 126


def test_pipeline_run_filters_bad_rows():
    bad = [{"id": 10, "score": 1}, {"id": 11}, {"score": 2}, {"id": 12, "score": 3}]
    res = bad_dup.pipeline_run(bad, "pipeline_mixed")
    # keeps only rows with both id & score -> [(10,1),(12,3)] -> parts [4], total 4
    assert res["parts"] == [4]
    assert res["total"] == 4


def test_normalize_nonempty():
    assert bad_dup.normalize([0, 5, 10]) == [0, 0.5, 1]


def test_normalize_empty():
    assert bad_dup.normalize([]) == []


def test_config_load_and_validate(capsys):
    cfg = bad_dup.Config(host="h", port=1234, retries=1)
    loaded = cfg.load()
    out = capsys.readouterr().out
    assert "Config.load" in out
    assert loaded == {"host": "h", "port": 1234, "retries": 1}
    assert cfg.validate() is True


def test_config_validate_bad_port(capsys):
    cfg = bad_dup.Config(port=-1)
    ok = cfg.validate()
    out = capsys.readouterr().out
    assert "Config.validate" in out
    assert ok is False


def test_main_direct_and_guard(capsys, monkeypatch):
    # 1) Call main() directly (covers body)
    bad_dup.main()
    out = capsys.readouterr().out
    assert "Report 1:" in out and "Report 10:" in out
    assert "pipeline_run_a: total" in out
    assert "pipeline_run_b: total" in out
    assert "pipeline_run_c: total" in out
    assert "main_e:" in out

    # 2) Execute file as a script to hit the __main__ guard
    # This re-runs the module under __main__ and should print the same markers.
    runpy.run_path(str(MODULE_PATH), run_name="__main__")
    out2 = capsys.readouterr().out
    assert "Report 1:" in out2 and "main_e:" in out2
