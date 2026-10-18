"""Prepare the complete site inventory after freezing the implementation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from fl_decipher.positional_worlds_v34 import prepare

ROOT = Path(__file__).resolve().parents[1]


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, v):
    target = ROOT / p
    assert not target.exists(), p
    target.write_text(json.dumps(v, indent=2) + '\n')


def main():
    cfg = read('experiments/positional_worlds_v34.json'); pre = read('data/v34/preflight.json')
    for inventory in [cfg['input_hashes'], pre['input_hashes'], pre['code_hashes']]:
        for p, h in inventory.items(): assert sha(p) == h, p
    assert not (ROOT / 'runs/000034_positional_worlds').exists()
    public, oracle = prepare(read('data/v32/public_cases.json'), read('data/v32/oracle.json'), read('data/v32/frozen_mapping.json')['model'], cfg)
    write('data/v34/public_observations.json', public); write('data/v34/oracle.json', oracle)
    outputs = {p: sha(p) for p in ['data/v34/public_observations.json', 'data/v34/oracle.json']}
    write('data/v34/preparation_receipt.json', {'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
                                               'output_hashes': outputs, 'site_rows': len(oracle['sites']),
                                               'predictions_computed': 0, 'frozen_mapping_sha256': sha('data/v32/frozen_mapping.json')})
    inputs = pre['input_hashes'] | outputs | {'data/v34/preflight.json': sha('data/v34/preflight.json'),
                                             'data/v34/preparation_receipt.json': sha('data/v34/preparation_receipt.json')}
    write('benchmarks/positional_worlds_v34.json', {'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'input_hashes': inputs})
    print(json.dumps({'site_rows': len(oracle['sites']), 'unique_observations': len(public['observations']), 'predictions_computed': 0}))


if __name__ == '__main__': main()
