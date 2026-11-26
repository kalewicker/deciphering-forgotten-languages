"""Verify the single-lead selection, blocked acquisition, and study disposition."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = "data/v103/"
REG = "experiments/yid_localization_v103.json"
OUT = "runs/000103_yid_localization/"


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    reg = read(REG)
    for path, expected in reg["input_hashes"].items():
        assert sha(path) == expected, path
    rows = read("runs/000102_yid_reservation/ledger.json")
    pool = sorted(row["number"] for row in rows
                  if row["failures"] == ["numeric_passage_and_wording_cue"])
    selection = read(DATA + "selection.json")
    assert len(pool) == 28 and selection["pool_ordinals"] == pool
    candidate = next(row for row in rows if row["number"] == min(pool))
    claim, = candidate["claims"]
    assert selection["claim"] == claim and selection["ordinal"] == reg["ordinal"] == candidate["number"]
    assert selection["component"] == candidate["component"]
    assert selection["native_locators"] == candidate["article_urls"]
    assert selection["target_denominator"] == reg["target_denominator"] == candidate["pairs"]
    urls = []
    for raw in claim["urls"]:
        url = urlsplit(raw)
        if url.scheme == "https" and url.hostname and not (url.username or url.password or url.fragment):
            urls.append(raw)
    intent = read(DATA + "acquisition/intent.json")
    receipt = read(DATA + "acquisition/receipt.json")
    assert intent["request_url"] == selection["selected_url"] == urls[0]
    assert intent["selection_sha256"] == sha(DATA + "selection.json")
    assert intent["acquirer_sha256"] == sha("scripts/acquire_yid_localization_v103.py")
    assert selection["selected_at_utc"] <= reg["registered_at_utc"] <= intent["started_at_utc"]
    assert intent["started_at_utc"] <= receipt["completed_at_utc"]
    assert selection["max_gets"] == receipt["requests_attempted"] == 1
    assert selection["redirects_allowed"] == 0 and selection["max_body_bytes"] == 16 * 1024 * 1024
    assert receipt["http_status"] == "403" and receipt["exit_code"] == 0
    header = (ROOT / DATA / "acquisition/headers.txt").read_text().splitlines()
    assert header[0].split()[1] == receipt["http_status"]
    body = DATA + "acquisition/body.bin"
    assert sha(body) == receipt["sha256"] and (ROOT / body).stat().st_size == receipt["bytes"]
    report = read(OUT + "report.json")
    assert report["outcome"] == "acquisition_blocked_http_403"
    assert report["http_status"] == 403 and report["requests_attempted"] == 1
    assert report["selected_ordinal"] == candidate["number"]
    assert report["reserved_catalog_ordinals"] == candidate["component"]
    assert report["target_denominator"] == candidate["pairs"] == 30
    assert report["identity_gate"] == report["comparison_status"] == "not_executed"
    assert report["whitespace_matches"] is None and report["token_matches"] is None
    assert report["pairing_runs"] == report["replication_panels_admitted"] == 0
    print(json.dumps({"verified": True, "catalog_pool": len(pool), "selected_ordinal": candidate["number"],
                      "http_status": 403, "retained_response_bytes": receipt["bytes"],
                      "localization_executed": False}))


if __name__ == "__main__":
    main()
