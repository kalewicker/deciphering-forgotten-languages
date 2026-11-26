"""Make the single registered source request and keep its receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    reg = json.loads((ROOT / "experiments/yid_localization_v103.json").read_text())
    for name, expected in reg["input_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    selection = json.loads((ROOT / "data/v103/selection.json").read_text())
    out = ROOT / "data/v103/acquisition"
    out.mkdir()
    (out / "intent.json").write_text(json.dumps({
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_sha256": reg["input_hashes"]["data/v103/selection.json"],
        "acquirer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "request_url": selection["selected_url"],
    }, indent=2) + "\n")
    response = subprocess.run([
        "/usr/bin/curl", "--disable", "--silent", "--show-error", "--proto", "=https",
        "--max-time", str(selection["timeout_seconds"]), "--max-filesize", str(selection["max_body_bytes"]),
        "--header", "Accept-Encoding: identity", "--dump-header", str(out / "headers.txt"),
        "--output", str(out / "body.bin"), "--write-out", "%{http_code}",
        selection["selected_url"],
    ], capture_output=True)
    body = out / "body.bin"
    body.touch(exist_ok=True)
    raw = body.read_bytes()
    result = {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
              "http_status": response.stdout.decode("ascii"), "exit_code": response.returncode,
              "stderr": response.stderr.decode("utf-8", errors="replace"),
              "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
              "requests_attempted": 1}
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
