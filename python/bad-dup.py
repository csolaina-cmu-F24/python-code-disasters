# bad_dupes.py
# NOTE: This file is intentionally awful for duplication experiments.
# - Tons of copy-paste
# - Near-identical functions/classes/blocks
# - Minimal differences to dodge trivial dedup
# Use at your own risk 🙂

DUMMY_DATA = [
    {"id": 1, "name": "alpha", "score": 42},
    {"id": 2, "name": "beta", "score": 42},
    {"id": 3, "name": "gamma", "score": 42},
]

# ---------------------------
# 10 NEAR-IDENTICAL FUNCTIONS
# ---------------------------

def do_report_1(items):
    # DUPLICATED BLOCK START
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 1",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 1:", summary)
    return summary
    # DUPLICATED BLOCK END

def do_report_2(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 2",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 2:", summary)
    return summary

def do_report_3(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 3",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 3:", summary)
    return summary

def do_report_4(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 4",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 4:", summary)
    return summary

def do_report_5(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 5",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 5:", summary)
    return summary

def do_report_6(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 6",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 6:", summary)
    return summary

def do_report_7(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 7",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 7:", summary)
    return summary

def do_report_8(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 8",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 8:", summary)
    return summary

def do_report_9(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 9",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 9:", summary)
    return summary

def do_report_10(items):
    total = 0
    count = 0
    names = []
    for it in items:
        if "score" in it:
            total += it["score"]
            count += 1
        if "name" in it:
            names.append(it["name"])
    avg = total / count if count else 0
    summary = {
        "title": "Report 10",
        "avg": avg,
        "count": count,
        "names": ",".join(names),
    }
    print("Report 10:", summary)
    return summary


# -------------------------
# 4 NEAR-IDENTICAL CLASSES
# -------------------------

class ConfigA:
    def __init__(self, host="localhost", port=8080, retries=3):
        self.host = host
        self.port = port
        self.retries = retries

    def load(self):
        print("ConfigA.load", self.host, self.port, self.retries)
        return {"host": self.host, "port": self.port, "retries": self.retries}

    def validate(self):
        ok = isinstance(self.port, int) and self.port > 0
        print("ConfigA.validate", ok)
        return ok


class ConfigB:
    def __init__(self, host="localhost", port=8080, retries=3):
        self.host = host
        self.port = port
        self.retries = retries

    def load(self):
        print("ConfigB.load", self.host, self.port, self.retries)
        return {"host": self.host, "port": self.port, "retries": self.retries}

    def validate(self):
        ok = isinstance(self.port, int) and self.port > 0
        print("ConfigB.validate", ok)
        return ok


class ConfigC:
    def __init__(self, host="localhost", port=8080, retries=3):
        self.host = host
        self.port = port
        self.retries = retries

    def load(self):
        print("ConfigC.load", self.host, self.port, self.retries)
        return {"host": self.host, "port": self.port, "retries": self.retries}

    def validate(self):
        ok = isinstance(self.port, int) and self.port > 0
        print("ConfigC.validate", ok)
        return ok


class ConfigD:
    def __init__(self, host="localhost", port=8080, retries=3):
        self.host = host
        self.port = port
        self.retries = retries

    def load(self):
        print("ConfigD.load", self.host, self.port, self.retries)
        return {"host": self.host, "port": self.port, "retries": self.retries}

    def validate(self):
        ok = isinstance(self.port, int) and self.port > 0
        print("ConfigD.validate", ok)
        return ok


# -----------------------------------
# 3 COPY-PASTED "PIPELINE" ROUTINES
# -----------------------------------

def pipeline_run_a(data):
    # DUPLICATED SEQUENCE START
    print("pipeline_run_a: start")
    cleaned = []
    for row in data:
        if "id" in row and "score" in row:
            cleaned.append({"id": row["id"], "score": row["score"], "name": row.get("name", "")})
    results = []
    for chunk in (cleaned[i:i+2] for i in range(0, len(cleaned), 2)):
        sub = 0
        for r in chunk:
            sub += r["score"]
        results.append(sub)
    total = sum(results)
    print("pipeline_run_a: total", total)
    return {"total": total, "parts": results}
    # DUPLICATED SEQUENCE END

def pipeline_run_b(data):
    print("pipeline_run_b: start")
    cleaned = []
    for row in data:
        if "id" in row and "score" in row:
            cleaned.append({"id": row["id"], "score": row["score"], "name": row.get("name", "")})
    results = []
    for chunk in (cleaned[i:i+2] for i in range(0, len(cleaned), 2)):
        sub = 0
        for r in chunk:
            sub += r["score"]
        results.append(sub)
    total = sum(results)
    print("pipeline_run_b: total", total)
    return {"total": total, "parts": results}

def pipeline_run_c(data):
    print("pipeline_run_c: start")
    cleaned = []
    for row in data:
        if "id" in row and "score" in row:
            cleaned.append({"id": row["id"], "score": row["score"], "name": row.get("name", "")})
    results = []
    for chunk in (cleaned[i:i+2] for i in range(0, len(cleaned), 2)):
        sub = 0
        for r in chunk:
            sub += r["score"]
        results.append(sub)
    total = sum(results)
    print("pipeline_run_c: total", total)
    return {"total": total, "parts": results}


# -----------------------------------
# 6 NEAR-IDENTICAL HELPERS (tiny diff)
# -----------------------------------

def normalize_1(x):
    m = max(x) if x else 1
    return [v / m for v in x]

def normalize_2(x):
    m = max(x) if x else 1
    return [v / m for v in x]

def normalize_3(x):
    m = max(x) if x else 1
    return [v / m for v in x]

def normalize_4(x):
    m = max(x) if x else 1
    return [v / m for v in x]

def normalize_5(x):
    m = max(x) if x else 1
    return [v / m for v in x]

def normalize_6(x):
    m = max(x) if x else 1
    return [v / m for v in x]


# -----------------------
# MAIN (also duplicated)
# -----------------------

def main_a():
    r1 = do_report_1(DUMMY_DATA)
    r2 = do_report_2(DUMMY_DATA)
    p = pipeline_run_a(DUMMY_DATA)
    print("main_a:", r1["avg"], r2["avg"], p["total"])

def main_b():
    r3 = do_report_3(DUMMY_DATA)
    r4 = do_report_4(DUMMY_DATA)
    p = pipeline_run_b(DUMMY_DATA)
    print("main_b:", r3["avg"], r4["avg"], p["total"])

def main_c():
    r5 = do_report_5(DUMMY_DATA)
    r6 = do_report_6(DUMMY_DATA)
    p = pipeline_run_c(DUMMY_DATA)
    print("main_c:", r5["avg"], r6["avg"], p["total"])

def main_d():
    r7 = do_report_7(DUMMY_DATA)
    r8 = do_report_8(DUMMY_DATA)
    p = pipeline_run_a(DUMMY_DATA)
    print("main_d:", r7["avg"], r8["avg"], p["total"])

def main_e():
    r9 = do_report_9(DUMMY_DATA)
    r10 = do_report_10(DUMMY_DATA)
    p = pipeline_run_b(DUMMY_DATA)
    print("main_e:", r9["avg"], r10["avg"], p["total"])

if __name__ == "__main__":
    # Pick one so the output is deterministic-ish
    main_a()
    main_b()
    main_c()
    main_d()
    main_e()
