"""Materialize reviewed correspondence locations, snapshot hashes, and split identities."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "benchmarks/kamri_excerpt_v1.json"
    if out.exists():
        raise SystemExit("Benchmark already frozen; use a new benchmark ID for changes.")
    spec = json.loads((ROOT / "benchmarks/audit_spec.json").read_text())
    config = json.loads((ROOT / "experiments/kamri_excerpt_v1.json").read_text())
    records = []
    for pair in spec["pairs"]:
        group = pair["group"]
        fl_path = ROOT / "data/normalized" / f"fl_{group}.json"
        en_path = ROOT / "data/normalized" / f"source_{group}.json"
        fl, en = json.loads(fl_path.read_text()), json.loads(en_path.read_text())
        fs, es = sentences(fl["text"], fl["id"]), sentences(en["text"], en["id"])
        starts = [i for i, s in enumerate(es) if s.text.startswith(pair["start"])]
        if len(starts) != 1 or len(fs) != pair["sentence_count"]:
            raise ValueError(f"Audit locator or sample count changed: {group}")
        links = []
        for i, f in enumerate(fs):
            e = es[starts[0] + i]
            eligible = i in pair["positional_eligible"]
            if eligible and len(f.tokens) != len(e.tokens):
                raise ValueError(f"Non-equal positional reference: {group}:{i}")
            links.append({"id": f"{group}:pair:{i:03d}", "fl_index": i, "source_index": starts[0] + i,
                          "fl_span": [f.start, f.end], "source_span": [e.start, e.end],
                          "fl_tokens": len(f.tokens), "source_tokens": len(e.tokens),
                          "state": "analyst_reviewed_structural_correspondence",
                          "positional_eligible": eligible, "semantic_gold": False})
        records.append({"group": group, "split": "test" if group in config["test_groups"] else "train",
                        "fl_path": str(fl_path.relative_to(ROOT)), "source_path": str(en_path.relative_to(ROOT)),
                        "fl_document_sha256": digest(fl_path.read_bytes()), "source_document_sha256": digest(en_path.read_bytes()),
                        "note": pair["note"], "links": links})
    dump_json(out, {"schema_version": 1, "annotation_method": spec["annotation_method"],
                    "config_sha256": digest((ROOT / "experiments/kamri_excerpt_v1.json").read_bytes()),
                    "records": records})
    print(out)


if __name__ == "__main__":
    main()
