"""Freeze and run the single Burton pairing development assay."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "experiments/burton_pairing_v101.md"
REG = "experiments/burton_pairing_v101.json"
PLAN = "data/v101/folds.json"
OUT = "runs/000101_burton_pairing"
REPLICATES = 999
EVIDENCE = [
    "data/v93/targets.json", "data/v96/targets.json",
    "runs/000100_burton_continuity/gap_ledger.json",
    "reports/000100_deliverable_seal.json", "reports/progress_review_after_e100.md",
]


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    with (ROOT / path).open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return digest((ROOT / path).read_bytes())


def tokens(text):
    return "".join(c if c.isalpha() else " " for c in text.casefold()).split()


def make_rows():
    yid = read(EVIDENCE[0])
    english = read(EVIDENCE[1])
    matches = read(EVIDENCE[2])["matches"]
    assert (yid["member"], yid["member_sha256"]) == (english["member"], english["member_sha256"])
    left = {row["ordinal"]: row["text"] for row in yid["targets"]}
    assert sorted(left) == list(range(1, 24))
    assert [row["ordinal"] for row in matches] == list(range(2, 24))
    assert [row["package_ordinal"] for row in english["targets"]] == list(range(2, 24))
    for match, target in zip(matches, english["targets"], strict=True):
        ordinal = target["package_ordinal"]
        yield {"ordinal": ordinal, "excerpt": match["window"],
               "yid": tokens(left[ordinal]), "english": tokens(target["text"]),
               "key": digest(target["text"].encode("utf-8"))}


def fold_plan(rows):
    folds = []
    for query in rows:
        alternatives = [row for row in rows if row != query and row["excerpt"] == query["excerpt"]]
        if not alternatives:
            folds.append({"query": query["ordinal"], "candidates": [], "training": []})
            continue
        distractor = min(alternatives, key=lambda row: (
            abs(len(row["english"]) - len(query["english"])), row["key"], row["ordinal"]))
        candidates = sorted([query, distractor], key=lambda row: (row["key"], row["ordinal"]))
        training = [row for row in rows if all(
            row["yid"] != held["yid"] and row["english"] != held["english"] for held in candidates)]
        training.sort(key=lambda row: (row["yid"], row["english"], row["key"]))
        folds.append({"query": query["ordinal"], "candidates": [r["ordinal"] for r in candidates],
                      "training": [r["ordinal"] for r in training]})
    return folds


def features(query, candidates, left, right):
    yid_vocab = set().union(*left)
    english_vocab = set().union(*right)
    shared = (yid_vocab | set(query)) & (english_vocab | set().union(*candidates))
    supported_query = {token for token in set(query) - shared
                       if sum(token in row for row in left) >= 2}
    supported_candidates = [(set(candidate) & english_vocab) - shared for candidate in candidates]
    return supported_query, supported_candidates


def rate_scores(query, candidates, left, right):
    counts = Counter(token for row in right for token in row)
    size = len(left)
    supports = {token: [i for i, row in enumerate(left) if token in row] for token in query}
    return [
        sum(Fraction(sum(english in right[i] for i in indices), len(indices))
            - Fraction(counts[english], size)
            for indices in supports.values() for english in candidate)
        / (len(query) * len(candidate))
        for candidate in candidates
    ]


def shuffled_right(training, right, query_id, replicate):
    permuted = list(right)
    for excerpt in (0, 1):
        indices = [i for i, row in enumerate(training) if row["excerpt"] == excerpt]
        order = sorted(indices, key=lambda i: digest(f"E101/{query_id}/{replicate}/{excerpt}/{i}".encode()))
        for destination, source in zip(indices, order, strict=True):
            permuted[destination] = right[source]
    return permuted


def encoded(values):
    return [str(value) for value in values]


def score_fold(rows, fold):
    query = rows[fold["query"]]
    choices = [rows[i] for i in fold["candidates"]]
    training = [rows[i] for i in fold["training"]]
    output = {**fold, "excerpt": query["excerpt"], "support": None,
              "observed": None, "length": None, "shuffled": None}
    if not choices or not training:
        return output
    left = [set(row["yid"]) for row in training]
    right = [set(row["english"]) for row in training]
    candidate_texts = [row["english"] for row in choices]
    eligible_query, eligible_candidates = features(query["yid"], candidate_texts, left, right)
    output["support"] = [len(eligible_query), *map(len, eligible_candidates)]
    if not eligible_query or not all(eligible_candidates):
        return output
    ratio = median(Fraction(len(row["english"]), len(row["yid"])) for row in training)
    expected = ratio * len(query["yid"])
    output["length"] = encoded([-abs(len(choice) - expected) for choice in candidate_texts])
    output["observed"] = encoded(rate_scores(eligible_query, eligible_candidates, left, right))
    output["shuffled"] = [
        encoded(rate_scores(eligible_query, eligible_candidates, left,
                            shuffled_right(training, right, query["ordinal"], replicate)))
        for replicate in range(REPLICATES)
    ]
    return output


def counts(folds, method, replicate=None):
    result = dict(wins=0, ties=0, losses=0, abstentions=0)
    for fold in folds:
        scores = fold[method]
        if scores is None:
            result["abstentions"] += 1
            continue
        if replicate is not None:
            scores = scores[replicate]
        first, second = map(Fraction, scores)
        if fold["candidates"][0] != fold["query"]:
            first, second = second, first
        result["wins" if first > second else "losses" if first < second else "ties"] += 1
    return result


def points(count):
    return Fraction(2 * count["wins"] + count["ties"] + count["abstentions"],
                    2 * sum(count.values()))


def summarize(folds):
    summaries = {}
    for name, group in [("all", folds), *((str(i), [f for f in folds if f["excerpt"] == i])
                                         for i in (0, 1))]:
        observed = counts(group, "observed")
        length = counts(group, "length")
        controls = [counts(group, "shuffled", i) for i in range(REPLICATES)]
        ordered = sorted(range(REPLICATES), key=lambda i: points(controls[i]))
        center, upper = ordered[499], ordered[949]
        summaries[name] = {
            "queries": len(group), "scored": len(group) - observed["abstentions"],
            "observed": observed, "length": length,
            "shuffle_median_replicate": center, "shuffle_median": controls[center],
            "shuffle_p95_replicate": upper, "shuffle_p95": controls[upper],
            "points": {key: str(points(value)) for key, value in [
                ("observed", observed), ("length", length),
                ("shuffle_median", controls[center]), ("shuffle_p95", controls[upper])]},
            "shuffle_at_or_above_observed": sum(points(c) >= points(observed) for c in controls),
        }
    overall = summaries["all"]
    values = {k: Fraction(v) for k, v in overall["points"].items()}
    gates = {
        "overall_coverage": overall["scored"] >= 16,
        "short_excerpt_coverage": summaries["1"]["scored"] >= 2,
        "minimum_score": values["observed"] >= Fraction(65, 100),
        "advantage_over_length": values["observed"] - values["length"] >= Fraction(15, 100),
        "advantage_over_shuffle_median": values["observed"] - values["shuffle_median"] >= Fraction(15, 100),
        "above_shuffle_p95": values["observed"] > values["shuffle_p95"],
    }
    return {"summaries": summaries, "gates": gates, "replication_justified": all(gates.values()),
            "semantic_benchmark_qualifying_works": 0, "new_untouched_units": 0}


def freeze():
    assert not (ROOT / REG).exists()
    old = read(EVIDENCE[3])["deliverable_hashes"]
    for path, value in old.items():
        assert sha(path) == value, path
    rows = list(make_rows())
    assert Counter(row["excerpt"] for row in rows) == {0: 18, 1: 4}
    assert all(row["yid"] and row["english"] for row in rows)
    (ROOT / PLAN).parent.mkdir()
    write(PLAN, {"rows": rows, "folds": fold_plan(rows)})
    paths = set(EVIDENCE + [PROTOCOL, PLAN, "scripts/burton_pairing_v101.py",
                           "scripts/verify_burton_pairing_v101.py", "tests/test_burton_pairing_v101.py"])
    paths.update(old)
    write(REG, {"registered_at_utc": datetime.now(timezone.utc).isoformat(), "target_denominator": 22,
                "shuffle_replicates": REPLICATES, "hashes": {p: sha(p) for p in sorted(paths)}})


def run():
    reg = read(REG)
    for path, value in reg["hashes"].items():
        assert sha(path) == value, path
    (ROOT / OUT).mkdir()
    plan = read(PLAN)
    rows = {row["ordinal"]: row for row in plan["rows"]}
    results = [score_fold(rows, fold) for fold in plan["folds"]]
    report = summarize(results)
    write(OUT + "/fold_results.json", results)
    write(OUT + "/report.json", report)
    write(OUT + "/manifest.json", {"registered_sha256": sha(REG),
                                  "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "hashes": {name: sha(OUT + "/" + name)
                                             for name in ("report.json", "fold_results.json")}})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "run"])
    {"freeze": freeze, "run": run}[parser.parse_args().action]()
