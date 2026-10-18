"""Lossless acquisition artifacts and versioned, offset-bearing text views."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(root: Path, url: str, *, acquisition_kind: str = "raw_http", content: bytes | None = None,
             locator: str | None = None) -> dict:
    """Explicit finite URL acquisition; experiments never invoke this function."""
    root.mkdir(parents=True, exist_ok=True)
    metadata = {"requested_url": url, "acquisition_kind": acquisition_kind,
                "acquired_at_utc": datetime.now(timezone.utc).isoformat(), "locator": locator}
    if content is None:
        header = root / "fetch_headers.tmp"
        result = subprocess.run([
            "curl", "--silent", "--show-error", "--fail", "--location", "--max-time", "30",
            "--user-agent", "FL-Decipher/0.1 finite research pilot",
            "--dump-header", str(header), "--write-out", "\n%{url_effective}\n%{http_code}", url,
        ], capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        content, final_url, status = result.stdout.rsplit(b"\n", 2)
        metadata.update(final_url=final_url.decode(), http_status=int(status),
                        response_headers=header.read_text(errors="replace"))
        header.unlink()
    else:
        metadata.update(final_url=None, http_status=None,
                        note="Imported extraction; this is not a raw HTTP response or proof of current page contents.")
    sha = digest(content)
    path = root / f"{sha}.bin"
    if not path.exists():
        path.write_bytes(content)
    metadata.update(sha256=sha, artifact=str(path), bytes=len(content))
    # Keep every acquisition receipt, including repeated retrievals of the same bytes.
    stamp = metadata["acquired_at_utc"].replace(":", "-")
    dump_json(root / f"{sha}.{stamp}.json", metadata)
    return metadata


def html_text(raw: bytes, selector: str | None = None, *, verse_labels: bool = False) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    node = soup.select_one(selector) if selector else soup.body or soup
    if node is None:
        raise ValueError(f"Missing HTML selector: {selector}")
    for tag in node.select("script, style, noscript, sup, .pageno, h1, h2, h3, h4, h5, h6"):
        tag.decompose()
    for tag in list(node.select("strong, b")):
        label = tag.get_text(" ", strip=True)
        if (len(label.split()) <= 8 and not re.search(r"[.!?;:]", label)
                and tag.parent.get_text(" ", strip=True) == label):
            tag.decompose()
    if verse_labels:
        for paragraph in node.find_all("p"):
            if re.fullmatch(r"[IVXLCDM]+", paragraph.get_text(strip=True)):
                paragraph.decompose()
                continue
            first = paragraph.find(string=True)
            if first:
                first.replace_with(re.sub(r"^\s*\d+\s+", "", str(first)))
    # Whitespace is a normalized view. Offsets refer to this saved view, not raw HTML.
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def normalized_document(doc_id: str, metadata: dict, text: str, *, kind: str,
                        group: str, transformations: list[str] | None = None) -> dict:
    return {"id": doc_id, "kind": kind, "source_group": group, "url": metadata["requested_url"],
            "snapshot": metadata, "text": text, "text_sha256": digest(text.encode()),
            "offset_basis": "Python Unicode code points in exact saved text field",
            "transformations": transformations or [], "parser_version": "pilot_text_v2"}
