"""Audit saved E99 offsets without searching for new matches."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = "experiments/burton_continuity_v100.json"
E99 = "runs/000099_burton_extract"
OUT = "runs/000100_burton_continuity"


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def coordinates(raw):
    runs = list(re.finditer(r"\S+", raw))
    pieces, spans = [], []
    for i, run in enumerate(runs):
        if i:
            pieces.append(" ")
            spans.append((runs[i - 1].end(), run.start()))
        pieces.append(run.group())
        spans.extend((j, j + 1) for j in range(run.start(), run.end()))
    return "".join(pieces), spans


def audit(extracted, comparison):
    raw_windows = extracted["windows"]
    normalized_windows = comparison["normalized_windows"]
    rows = comparison["whitespace"]["rows"]
    assert len(raw_windows) == len(normalized_windows) == 2
    assert len(rows) == comparison["whitespace"]["denominator"] == 22
    maps = []
    for raw, saved in zip(raw_windows, normalized_windows, strict=True):
        normalized, mapping = coordinates(raw)
        assert normalized == saved
        maps.append(mapping)

    matches = []
    for ordinal, row in enumerate(rows, 2):
        hit = row["ordered_occurrence"]
        assert hit and row["occurrences"] == [hit]
        window = hit["window"]
        assert window == (0 if ordinal <= 19 else 1)
        start, end = hit["span"]
        assert 0 <= start < end <= len(maps[window])
        left, right = maps[window][start][0], maps[window][end - 1][1]
        assert " ".join(raw_windows[window][left:right].split()) == normalized_windows[window][start:end]
        matches.append({"ordinal": ordinal, "window": window,
                        "normalized_span": [start, end], "raw_span": [left, right]})

    def gap(window, kind, before, after):
        raw_start = before["raw_span"][1] if before else 0
        raw_end = after["raw_span"][0] if after else len(raw_windows[window])
        norm_start = before["normalized_span"][1] if before else 0
        norm_end = after["normalized_span"][0] if after else len(normalized_windows[window])
        assert raw_start <= raw_end and norm_start <= norm_end
        text = raw_windows[window][raw_start:raw_end]
        return {
            "window": window, "kind": kind,
            "before": before["ordinal"] if before else None,
            "after": after["ordinal"] if after else None,
            "raw_span": [raw_start, raw_end],
            "normalized_span": [norm_start, norm_end],
            "full_extracted_span": [extracted["window_spans"][window][0] + s for s in (raw_start, raw_end)],
            "text": text, "characters": len(text),
            "classification": "empty" if not text else "whitespace_only" if text.isspace() else "non_whitespace",
            "alphanumeric_characters": sum(c.isalnum() for c in text),
            "nonspace_runs": len(text.split()),
        }

    transitions = []
    for before, after in zip(matches, matches[1:]):
        if before["window"] == after["window"]:
            transitions.append(gap(before["window"], "internal", before, after))
        else:
            transitions.append({"kind": "declared_page_jump", "before": before["ordinal"],
                                "after": after["ordinal"], "raw_span": None})
    edges = [gap(0, "prefix", None, matches[0]), gap(0, "suffix", matches[17], None),
             gap(1, "prefix", None, matches[18]), gap(1, "suffix", matches[-1], None)]
    return {"matches": matches, "transitions": transitions, "edges": edges}


def summarize(ledger):
    internal = [row for row in ledger["transitions"] if row["kind"] == "internal"]
    classes = ("empty", "whitespace_only", "non_whitespace")
    by_window = {}
    for window in range(2):
        gaps = [g for g in internal if g["window"] == window]
        by_window[str(window)] = {
            "internal_gaps": len(gaps),
            **{name: sum(g["classification"] == name for g in gaps) for name in classes},
            "gap_characters": sum(g["characters"] for g in gaps),
            "gap_alphanumeric_characters": sum(g["alphanumeric_characters"] for g in gaps),
            "gap_nonspace_runs": sum(g["nonspace_runs"] for g in gaps),
        }
    return {
        "targets": len(ledger["matches"]), "transitions": len(ledger["transitions"]),
        "internal_gaps": len(internal), "edge_spans": len(ledger["edges"]),
        "declared_jumps": sum(row["kind"] == "declared_page_jump" for row in ledger["transitions"]),
        "windows": by_window,
        "strict_continuity": all(g["classification"] != "non_whitespace" for g in internal),
        "new_wording_searches": 0, "network_requests": 0,
        "semantic_benchmark_qualifying_works": 0, "new_untouched_units": 0,
    }


def run():
    registration = read(REGISTRATION)
    for path, expected in registration["input_hashes"].items():
        assert digest(path) == expected, path
    (ROOT / OUT).mkdir()
    ledger = audit(read(E99 + "/extraction.json"), read(E99 + "/comparison.json"))
    report = summarize(ledger)
    for name, value in (("gap_ledger", ledger), ("report", report)):
        with (ROOT / OUT / (name + ".json")).open("x") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    manifest = {
        "state": "complete",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "registration_sha256": digest(REGISTRATION),
        "outputs": {path: digest(path) for path in (OUT + "/gap_ledger.json", OUT + "/report.json")},
    }
    with (ROOT / OUT / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
