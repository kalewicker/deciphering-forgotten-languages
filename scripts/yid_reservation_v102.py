"""Outcome-free catalog screening for one reserved replication lead."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REG = "experiments/yid_reservation_v102.json"
OUT = "runs/000102_yid_reservation"
LEDGER = "runs/000092_yid_adapter/ledger.json"
SAMPLE = "data/v92/development_sample.json"
AUDIT = "data/v95/selected_claims.json"
FL_HOSTS = {"forgottenlanguages-full.forgottenlanguages.org", "forgottenlanguages.org"}
PAGE_RANGE = re.compile(r"\b(?:pages?|pp?\.)\s+\d+\s*(?:[-–—]|to)\s*\d+\b", re.I)
WORDING = re.compile(r"\b(?:exact|verbatim|ordered|continuous|aligned|lock)\b", re.I)


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, data):
    with (ROOT / path).open("x") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def locator(value):
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        host = url.hostname
    except ValueError:
        return None
    if url.scheme not in {"http", "https"} or not host or url.username or url.password:
        return None
    path = unquote(url.path).rstrip("/") or "/"
    if host in FL_HOSTS:
        host = "forgottenlanguages.org"
    return host, path


def citation_key(value):
    return " ".join("".join(c if c.isalnum() else " " for c in value.casefold()).split())


def screen():
    ledger = read(LEDGER)
    # A raw catalog member is used only to recover the frozen citation spans.
    import zipfile
    with zipfile.ZipFile(ROOT / "data/v90/acquisition/hop_01/body.bin") as archive:
        catalog = archive.read(ledger["source_member"]).decode("utf-8")
    rows = {row["number"]: row for row in ledger["sources"]["rows"]}
    assert sorted(rows) == list(range(1, 87))
    development = {s["member"] for s in read(SAMPLE)}
    audited = {r["number"] for r in read(AUDIT)}
    known = {locator(r["url"]) for r in read("reports/000037_exposure_ledger.json")["records"]}
    known.update(map(locator, read("data/v63_registration/known_exposure.json")["urls"]))
    known.update(map(locator, read("data/v80/exposure.json")["known_article_keys"]))
    known.discard(None)

    records = {}
    links = defaultdict(set)
    for article in ledger["articles"]:
        number, join = article["number"], article["join"]
        article_urls = join["candidate_locators"]
        direct = []
        if article["member"] in development:
            direct.append("development_member")
        if number in audited:
            direct.append("inspected_claims")
        if any(locator(url) in known for url in article_urls):
            direct.append("known_article_locator")
        claims = []
        for claim in rows[number]["claims"]:
            urls = [r["value"] for r in claim["url_literals"]]
            external = [u for u in urls if (key := locator(u)) and key[0] != "forgottenlanguages.org"]
            if not external:
                continue
            a, b = claim["citation_span"]
            citation = catalog[a:b]
            roles = [f["value"] for f in claim["fields"] if f["key"].casefold() == "role"]
            claims.append({"citation": citation, "urls": external, "roles": roles,
                           "span": claim["span"]})
            for url in external:
                key = locator(url)
                links[("url", key)].add(number)
                if key in known and "known_source_locator" not in direct:
                    direct.append("known_source_locator")
            if key := citation_key(citation):
                links[("citation", key)].add(number)
        records[number] = {"number": number, "pairs": join["parsed_pairs"],
                           "join_resolved": join["resolved_layout_and_join"],
                           "article_urls": article_urls, "direct_exposure": direct, "claims": claims}

    neighbors = defaultdict(set)
    for members in links.values():
        for number in members:
            neighbors[number].update(members)
    for number, row in sorted(records.items()):
        component, pending = set(), {number}
        while pending:
            member = pending.pop()
            component.add(member)
            pending.update(neighbors[member] - component)
        row["component"] = sorted(component)
        row["exposed_members"] = sorted(n for n in component if records[n]["direct_exposure"])
        failures = []
        if not row["join_resolved"] or len(row["article_urls"]) != 1 or not locator(row["article_urls"][0]):
            failures.append("article_join")
        if row["pairs"] < 22:
            failures.append("pair_floor")
        if row["exposed_members"]:
            failures.append("known_exposure")
        if len(row["claims"]) != 1:
            failures.append("external_claim_count")
        else:
            claim = row["claims"][0]
            if not claim["citation"].strip() or not any(u.startswith("https://") for u in claim["urls"]):
                failures.append("citation_or_https")
            if not any(PAGE_RANGE.search(role) and WORDING.search(role) for role in claim["roles"]):
                failures.append("numeric_passage_and_wording_cue")
        row["failures"] = failures
    return [records[i] for i in sorted(records)]


def main():
    registration = read(REG)
    for path, expected in registration["hashes"].items():
        assert sha(path) == expected, path
    rows = screen()
    assert [row["number"] for row in rows] == list(range(1, 87))
    candidates = [row for row in rows if not row["failures"]]
    report = {
        "catalog_documents": len(rows),
        "components": len({tuple(row["component"]) for row in rows}),
        "direct_exposure_rows": sum(bool(row["direct_exposure"]) for row in rows),
        "failure_counts": dict(Counter(reason for row in rows for reason in row["failures"])),
        "qualifying_metadata_leads": len(candidates),
        "nominee_number": candidates[0]["number"] if candidates else None,
        "reserved_catalog_ordinals": candidates[0]["component"] if candidates else [],
        "replication_panels_admitted": 0, "pairing_runs": 0,
        "network_requests": 0, "semantic_benchmark_qualifying_works": 0,
    }
    if sys.argv[1:] == ["verify"]:
        assert read(OUT + "/ledger.json") == rows
        assert read(OUT + "/report.json") == report
        manifest = read(OUT + "/manifest.json")
        assert sha(REG) == manifest["registration_sha256"]
        for path, expected in manifest["hashes"].items():
            assert sha(path) == expected, path
        print("Replayed all 86 catalog dispositions and the nomination.")
        return
    if sys.argv[1:]:
        raise SystemExit("Usage: yid_reservation_v102.py [verify]")
    (ROOT / OUT).mkdir()
    ledger_path, report_path = OUT + "/ledger.json", OUT + "/report.json"
    write(ledger_path, rows)
    write(report_path, report)
    write(OUT + "/manifest.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "registration_sha256": sha(REG),
                                  "hashes": {p: sha(p) for p in (ledger_path, report_path)}})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
