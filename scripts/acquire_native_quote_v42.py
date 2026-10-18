"""Perform the single registered native request; never retries or follows links."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.capture_review_v23 import request
from fl_decipher.native_quote_v42 import inspect_page

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = json.loads((ROOT / 'experiments/native_quote_v42.json').read_text())
    assert not (ROOT / 'data/v42').exists()
    for path, expected in cfg['input_hashes'].items():
        assert sha(path) == expected, path
    paths = ['experiments/native_quote_v42.json', 'scripts/acquire_native_quote_v42.py',
             'src/fl_decipher/native_quote_v42.py', 'tests/test_native_quote_v42.py',
             'src/fl_decipher/capture_review_v23.py', 'src/fl_decipher/dated_capture_scope_v38.py']
    hashes = cfg['input_hashes'] | {p: sha(p) for p in paths}
    write('data/v42/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(), 'hashes': hashes})
    receipt = request(ROOT / 'data/v42/acquisition', 'source', cfg['source_url'], cfg['request_limits'], 'native')
    path = ROOT / 'data/v42/acquisition/source/body.bin'
    result = inspect_page(path.read_bytes() if path.exists() else b'', receipt, cfg)
    write('data/v42/page_observations.json', result)
    if result['text'] is not None:
        with (ROOT / 'data/v42/visible_page.txt').open('x') as stream:
            stream.write(result['text'])
    print(json.dumps({'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
                      'material_available': result['material_available'], 'quote_present': result['quote_present'],
                      'contexts': len(result['contexts']), 'unmet': result['unmet']}, indent=2))


if __name__ == '__main__':
    main()
