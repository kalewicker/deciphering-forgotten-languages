"""Import explicitly labeled indexed FL excerpts; never call them raw snapshots."""
import json
from pathlib import Path

from fl_decipher.corpus import dump_json, normalized_document, snapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    inputs = json.loads((ROOT / "benchmarks/inputs/indexed_fl_excerpts.json").read_text())["inputs"]
    for entry in inputs:
        path = ROOT / "data/normalized" / (entry["id"] + ".json")
        if path.exists():
            print(entry["id"], "cached")
            continue
        receipt = snapshot(ROOT / "data/raw", entry["url"], acquisition_kind="indexed_web_excerpt",
                           content=entry["text"].encode(), locator=entry["locator"])
        text = entry["text"]
        changes = ["opening excerpt selection; see input manifest"]
        if entry["group"] == "gad_seer":
            # Visible split drop cap, retained in the imported bytes; declared repair in text view.
            text = text.replace("Ş elomo", "Şelomo", 1)
            changes.append("join extracted opening drop cap Ş elomo -> Şelomo")
        dump_json(path, normalized_document(entry["id"], receipt, text, kind="fl", group=entry["group"],
                                            transformations=changes))
        print(entry["id"], "imported", entry["selection_words"], "excerpt words")


if __name__ == "__main__":
    main()
