"""Replay saved intervals with a character scanner and verify window partitions."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = "runs/000100_burton_continuity/"
REGISTRATION = "experiments/burton_continuity_v100.json"


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def coordinate_scan(text):
    coordinates = []
    previous = None
    for offset, character in enumerate(text):
        if character.isspace():
            continue
        if previous is not None and offset > previous + 1:
            coordinates.append((previous + 1, offset))
        coordinates.append((offset, offset + 1))
        previous = offset
    return coordinates


def main():
    registration = read(REGISTRATION)
    manifest = read(OUT + "manifest.json")
    assert manifest["state"] == "complete"
    assert registration["registered_at_utc"] <= manifest["completed_at_utc"]
    assert digest(REGISTRATION) == manifest["registration_sha256"]
    for mapping in (registration["input_hashes"], manifest["outputs"]):
        for path, expected in mapping.items():
            assert digest(path) == expected, path

    extracted = read("runs/000099_burton_extract/extraction.json")
    comparison = read("runs/000099_burton_extract/comparison.json")
    ledger = read(OUT + "gap_ledger.json")
    report = read(OUT + "report.json")
    assert len(ledger["matches"]) == 22
    assert len(ledger["transitions"]) == 21
    assert len(ledger["edges"]) == 4
    assert [g for g in ledger["transitions"] if g["kind"] == "declared_page_jump"] == [
        {"kind": "declared_page_jump", "before": 19, "after": 20, "raw_span": None}
    ]
    assert [(g["before"], g["after"]) for g in ledger["transitions"]] == [
        (i, i + 1) for i in range(2, 23)
    ]
    non_whitespace = 0
    for window, raw in enumerate(extracted["windows"]):
        mapping = coordinate_scan(raw)
        normalized = comparison["normalized_windows"][window]
        assert "".join(raw[a:b] if b == a + 1 and not raw[a].isspace() else " "
                       for a, b in mapping) == normalized
        matches = [m for m in ledger["matches"] if m["window"] == window]
        ordinals = list(range(2, 20)) if window == 0 else list(range(20, 24))
        assert [m["ordinal"] for m in matches] == ordinals
        by_ordinal = {m["ordinal"]: m for m in matches}
        for match in matches:
            saved = comparison["whitespace"]["rows"][match["ordinal"] - 2]
            hit = saved["ordered_occurrence"]
            assert saved["occurrences"] == [hit] and hit["window"] == window
            start, end = hit["span"]
            assert match["normalized_span"] == [start, end]
            assert match["raw_span"] == [mapping[start][0], mapping[end - 1][1]]
        internal = [g for g in ledger["transitions"] if g["kind"] == "internal" and g["window"] == window]
        edges = [g for g in ledger["edges"] if g["window"] == window]
        assert len(internal) == len(matches) - 1
        assert [(e["kind"], e["before"], e["after"]) for e in edges] == [
            ("prefix", None, ordinals[0]), ("suffix", ordinals[-1], None)
        ]
        for gap in internal + edges:
            before = by_ordinal.get(gap["before"])
            after = by_ordinal.get(gap["after"])
            a = before["raw_span"][1] if before else 0
            b = after["raw_span"][0] if after else len(raw)
            assert gap["raw_span"] == [a, b]
            assert gap["normalized_span"] == [
                before["normalized_span"][1] if before else 0,
                after["normalized_span"][0] if after else len(normalized),
            ]
            origin = extracted["window_spans"][window][0]
            assert gap["full_extracted_span"] == [origin + a, origin + b]
            text = raw[a:b]
            assert gap["text"] == text and gap["characters"] == b - a
            classification = ("non_whitespace" if text.strip()
                              else "whitespace_only" if text else "empty")
            assert gap["classification"] == classification
            assert gap["alphanumeric_characters"] == sum(map(str.isalnum, text))
            assert gap["nonspace_runs"] == len(text.split())
        cursor = 0
        for start, end in sorted(entry["raw_span"] for entry in matches + internal + edges):
            assert start == cursor and end >= start
            cursor = end
        assert cursor == len(raw)
        summary = report["windows"][str(window)]
        assert summary["internal_gaps"] == len(internal)
        for kind in ("empty", "whitespace_only", "non_whitespace"):
            assert summary[kind] == sum(g["classification"] == kind for g in internal)
        for name in ("characters", "alphanumeric_characters", "nonspace_runs"):
            assert summary["gap_" + name] == sum(g[name] for g in internal)
        non_whitespace += summary["non_whitespace"]
    assert report["strict_continuity"] == (non_whitespace == 0)
    assert (report["targets"], report["transitions"], report["internal_gaps"],
            report["edge_spans"], report["declared_jumps"]) == (22, 21, 20, 4, 1)
    print(json.dumps({"verified": True, "targets": 22, "internal_gaps": 20,
                      "edge_spans": 4, "non_whitespace_internal_gaps": non_whitespace}))


if __name__ == "__main__":
    main()
