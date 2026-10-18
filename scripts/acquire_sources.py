"""Acquire only the five nominated English works, caching receipts and raw bytes."""
from pathlib import Path
import re
import time

from fl_decipher.corpus import dump_json, html_text, normalized_document, snapshot

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ("golden_age", "https://www.alchemywebsite.com/goldnage.html", None),
    ("nichiren_images", "https://www.nichirenlibrary.org/en/wnd-1/Content/11", "article"),
    ("gad_seer", "https://www.pseudepigrapha.com/WordsOfTheSeerGad.html", None),
    ("dark_side_light", "https://www.theosophical.org/publications/quest-magazine/the-dark-side-of-light", ".com-content-article__body"),
    ("christisis", "https://archive.org/download/christisishigher00clym/christisishigher00clym_djvu.txt", None),
]


def main():
    ledger = []
    for group, url, selector in SOURCES:
        out = ROOT / "data/normalized" / f"source_{group}.json"
        if out.exists():
            ledger.append({"id": group, "status": "cached", "path": str(out.relative_to(ROOT))})
            continue
        try:
            receipt = snapshot(ROOT / "data/raw", url)
            raw = Path(receipt["artifact"]).read_bytes()
            if group == "christisis":
                text = raw.decode("utf-8")
                # Repair line-wrapped hyphenation; all edits have a named normalized view.
                text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
                text = re.sub(r"\s+", " ", text).strip()
                changes = ["archive OCR, not checked against scan", "join line-wrap hyphens", "collapse whitespace"]
            else:
                text = html_text(raw, selector, verse_labels=group == "gad_seer")
                changes = ["HTML text extraction", f"selector={selector or 'body'}", "remove superscript notes/page labels/headings", "collapse whitespace"]
                if group == "gad_seer":
                    changes.append("remove verse-number prefixes and standalone Roman chapter headings")
            dump_json(out, normalized_document("source_" + group, receipt, text, kind="source", group=group,
                                                transformations=changes))
            ledger.append({"id": group, "status": "downloaded", "sha256": receipt["sha256"]})
        except (RuntimeError, ValueError, UnicodeError) as exc:
            ledger.append({"id": group, "status": "failed", "error": str(exc)})
        time.sleep(1)
    dump_json(ROOT / "data/acquisition_sources.json", ledger)
    for entry in ledger:
        print(entry["id"], entry["status"])
    if any(x["status"] == "failed" for x in ledger):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
