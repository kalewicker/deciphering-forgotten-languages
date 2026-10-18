"""Finite source attempts only; never replaces an acquisition or runs a scorer."""
from pathlib import Path
from fl_decipher.natural_v12 import NOMINATIONS, fetch

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    for work in NOMINATIONS:
        for i, url in enumerate(work['source_routes'], 1):
            receipt = fetch(ROOT/'data/v12/acquisition', work['id']+f'_{i}', url)
            print(work['id'], i, 'HTTP', receipt['http_status'], 'curl', receipt['curl_returncode'], flush=True)
