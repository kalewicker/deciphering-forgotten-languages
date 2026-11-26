"""Reconstruct the registered panel, all scores, and the aggregate decision."""
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import groupby
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
OUT = "runs/000101_burton_pairing/"
REG = "experiments/burton_pairing_v101.json"


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def words(text):
    return ["".join(run) for letter, run in groupby(text.casefold(), str.isalpha) if letter]


def tally(folds, method, index=None):
    totals = Counter({"wins": 0, "ties": 0, "losses": 0, "abstentions": 0})
    for row in folds:
        values = row[method]
        if values is None:
            totals["abstentions"] += 1
            continue
        if index is not None:
            values = values[index]
        gold = row["candidates"].index(row["query"])
        delta = Fraction(values[gold]) - Fraction(values[1 - gold])
        totals[("losses", "ties", "wins")[(delta > 0) - (delta < 0) + 1]] += 1
    return dict(totals)


def points(totals):
    return Fraction(1, 2) + Fraction(totals["wins"] - totals["losses"], 2 * sum(totals.values()))


def main():
    reg = read(REG)
    manifest = read(OUT + "manifest.json")
    assert reg["registered_at_utc"] <= manifest["completed_at_utc"]
    assert manifest["registered_sha256"] == sha(REG)
    for path, value in reg["hashes"].items():
        assert sha(path) == value, path
    for path, value in manifest["hashes"].items():
        assert sha(OUT + path) == value, path
    assert reg["target_denominator"] == 22 and reg["shuffle_replicates"] == 999

    left = {r["ordinal"]: words(r["text"]) for r in read("data/v93/targets.json")["targets"]}
    texts = {r["package_ordinal"]: r["text"] for r in read("data/v96/targets.json")["targets"]}
    right = {i: words(text) for i, text in texts.items()}
    keys = {i: digest(text) for i, text in texts.items()}
    groups = {r["ordinal"]: r["window"] for r in
              read("runs/000100_burton_continuity/gap_ledger.json")["matches"]}
    plan = read("data/v101/folds.json")
    ids = list(range(2, 24))
    assert list(texts) == list(groups) == ids and Counter(groups.values()) == {0: 18, 1: 4}
    assert plan["rows"] == [{"ordinal": i, "excerpt": groups[i], "yid": left[i],
                             "english": right[i], "key": keys[i]} for i in ids]
    results = read(OUT + "fold_results.json")
    assert [r["query"] for r in results] == ids
    for i, record, fold in zip(ids, results, plan["folds"], strict=True):
        candidates = [(abs(len(right[i]) - len(right[j])), keys[j], j)
                      for j in ids if groups[i] == groups[j] and i != j]
        foil = sorted(candidates)[0][2]
        pair = sorted([i, foil], key=lambda j: (keys[j], j))
        training = sorted((j for j in ids if j not in pair
                           and left[j] not in [left[k] for k in pair]
                           and right[j] not in [right[k] for k in pair]),
                          key=lambda j: (left[j], right[j], keys[j]))
        assert fold == {"query": i, "candidates": pair, "training": training}
        assert all(record[k] == v for k, v in fold.items()) and record["excerpt"] == groups[i]
        train_yid = [set(left[j]) for j in training]
        train_eng = [set(right[j]) for j in training]
        vocab_yid = Counter(t for row in train_yid for t in row)
        vocab_eng = Counter(t for row in train_eng for t in row)
        ban = (vocab_yid.keys() | set(left[i])) & (vocab_eng.keys() | set(right[i]) | set(right[foil]))
        query = {t for t in set(left[i]) - ban if vocab_yid[t] >= 2}
        options = [set(right[j]) & vocab_eng.keys() - ban for j in pair]
        assert record["support"] == [len(query), *map(len, options)]
        if not query or not all(options):
            assert all(record[method] is None for method in ("observed", "length", "shuffled"))
            continue

        # Each training row contributes its query-conditioned weight minus its
        # marginal weight, multiplied by its fraction of supported English forms.
        weights = [sum((Fraction(1, vocab_yid[t]) for t in query & row), Fraction()) / len(query)
                   - Fraction(1, len(training)) for row in train_yid]
        overlaps = [[Fraction(len(option & row), len(option)) for row in train_eng]
                    for option in options]

        def score(order):
            return [str(sum(weights[pos] * values[source] for pos, source in enumerate(order)))
                    for values in overlaps]

        identity = list(range(len(training)))
        assert record["observed"] == score(identity)
        ratio = median(Fraction(len(right[j]), len(left[j])) for j in training)
        assert record["length"] == [str(-abs(len(right[j]) - ratio * len(left[i]))) for j in pair]
        assert len(record["shuffled"]) == 999
        positions = [[pos for pos, j in enumerate(training) if groups[j] == group] for group in (0, 1)]
        for replicate, values in enumerate(record["shuffled"]):
            order = identity.copy()
            for group, selected in enumerate(positions):
                ordered = sorted((digest(f"E101/{i}/{replicate}/{group}/{pos}"), pos)
                                 for pos in selected)
                for dest, (_, source) in zip(selected, ordered, strict=True):
                    order[dest] = source
            assert values == score(order), (i, replicate)

    report = read(OUT + "report.json")
    for label in ("all", "0", "1"):
        subset = [r for r in results if label == "all" or str(r["excerpt"]) == label]
        observed, length = [tally(subset, method) for method in ("observed", "length")]
        shuffled = [tally(subset, "shuffled", i) for i in range(999)]
        order = sorted((points(item), i) for i, item in enumerate(shuffled))
        middle, upper = order[499][1], order[949][1]
        expected = report["summaries"][label]
        assert expected["queries"] == len(subset)
        assert expected["scored"] == len(subset) - observed["abstentions"]
        assert expected["shuffle_median_replicate"] == middle
        assert expected["shuffle_p95_replicate"] == upper
        for key, count in zip(("observed", "length", "shuffle_median", "shuffle_p95"),
                              (observed, length, shuffled[middle], shuffled[upper]), strict=True):
            assert expected[key] == count and Fraction(expected["points"][key]) == points(count)
        assert expected["shuffle_at_or_above_observed"] == sum(p >= points(observed) for p, _ in order)

    overall = report["summaries"]["all"]
    observed, length, middle, upper = (Fraction(overall["points"][k]) for k in
                                       ("observed", "length", "shuffle_median", "shuffle_p95"))
    gates = dict(overall_coverage=overall["scored"] >= 16,
                 short_excerpt_coverage=report["summaries"]["1"]["scored"] >= 2,
                 minimum_score=observed >= Fraction(13, 20),
                 advantage_over_length=observed >= length + Fraction(3, 20),
                 advantage_over_shuffle_median=observed >= middle + Fraction(3, 20),
                 above_shuffle_p95=observed > upper)
    assert report["gates"] == gates and report["replication_justified"] == all(gates.values())
    assert report["semantic_benchmark_qualifying_works"] == report["new_untouched_units"] == 0
    print(json.dumps({"verified": True, "queries": 22, "scored_queries": overall["scored"],
                      "replayed_shuffled_folds": 999 * overall["scored"]}))


if __name__ == "__main__":
    main()
