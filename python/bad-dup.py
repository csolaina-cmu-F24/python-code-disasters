# clean_reports.py
# A cleaned-up, duplication-free version of the earlier file.

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

DUMMY_DATA: List[Dict[str, Any]] = [
    {"id": 1, "name": "alpha", "score": 42},
    {"id": 2, "name": "beta",  "score": 42},
    {"id": 3, "name": "gamma", "score": 42},
]


# -----------------
# Shared utilities
# -----------------

def summarize(items: Iterable[Dict[str, Any]], title: str) -> Dict[str, Any]:
    total = 0
    count = 0
    names: List[str] = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": title,
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print(f"{title}:", summary)
    return summary


def pipeline_run(data: Iterable[Dict[str, Any]], label: str) -> Dict[str, Any]:
    """Mimics the old pipelines but without copy-paste; label controls print text."""
    print(f"{label}: start")
    cleaned = [
        {"id": row["id"], "score": row["score"], "name": row.get("name", "")}
        for row in data
        if "id" in row and "score" in row
    ]
    results: List[int] = []
    for i in range(0, len(cleaned), 2):
        chunk = cleaned[i:i + 2]
        sub = sum(r["score"] for r in chunk)
        results.append(sub)
    total = sum(results)
    print(f"{label}: total", total)
    return {"total": total, "parts": results}


def normalize(values: List[float]) -> List[float]:
    m = max(values) if values else 1
    return [v / m for v in values]


# -------------
# Single config
# -------------

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    retries: int = 3

    def load(self) -> Dict[str, Any]:
        print("Config.load", self.host, self.port, self.retries)
        return {"host": self.host, "port": self.port, "retries": self.retries}

    def validate(self) -> bool:
        ok = isinstance(self.port, int) and self.port > 0
        print("Config.validate", ok)
        return ok


# -----
# Main
# -----

def main() -> None:
    # Produce the same 10 “Report X:” prints, but via one function.
    reports = [summarize(DUMMY_DATA, f"Report {i}") for i in range(1, 11)]

    # Produce the three pipeline runs with the same labels as before.
    p_a = pipeline_run(DUMMY_DATA, "pipeline_run_a")
    p_b = pipeline_run(DUMMY_DATA, "pipeline_run_b")
    p_c = pipeline_run(DUMMY_DATA, "pipeline_run_c")

    # Preserve the old “main_*” summary lines without duplicating functions.
    print("main_a:", reports[0]["avg"], reports[1]["avg"], p_a["total"])
    print("main_b:", reports[2]["avg"], reports[3]["avg"], p_b["total"])
    print("main_c:", reports[4]["avg"], reports[5]["avg"], p_c["total"])
    print("main_d:", reports[6]["avg"], reports[7]["avg"], p_a["total"])
    print("main_e:", reports[8]["avg"], reports[9]["avg"], p_b["total"])


if __name__ == "__main__":
    main()
