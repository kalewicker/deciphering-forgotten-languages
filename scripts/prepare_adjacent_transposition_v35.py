"""Freeze all v34 observations and deterministic v35 controls before scoring."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from fl_decipher.adjacent_transposition_v35 import prepare

ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p, v):
    target = ROOT/p; assert not target.exists(), p
    target.write_text(json.dumps(v, indent=2)+'\n')


def main():
    cfg = read('experiments/adjacent_transposition_v35.json'); pre = read('data/v35/preflight.json')
    for hashes in [cfg['input_hashes'], pre['input_hashes'], pre['code_hashes']]:
        for p, h in hashes.items(): assert sha(p) == h, p
    assert not (ROOT/'runs/000035_adjacent_transposition').exists()
    old_public = read('data/v34/public_observations.json'); old_gold = read('data/v34/oracle.json')
    public, oracle = prepare(old_public, old_gold, read('data/v32/frozen_mapping.json')['model'])
    assert len(oracle['controls']) == cfg['control_rows'] and len(public['panels']) == cfg['panels']
    assert oracle['v34_sites'] == old_gold['sites'] and all(public['observations'][k] == v for k, v in old_public['observations'].items())
    write('data/v35/public_observations.json', public); write('data/v35/oracle.json', oracle)
    outputs = {p: sha(p) for p in ['data/v35/public_observations.json', 'data/v35/oracle.json']}
    write('data/v35/preparation_receipt.json', {'prepared_at_utc': datetime.now(timezone.utc).isoformat(), 'output_hashes': outputs,
                                               'v34_observations_preserved': len(old_public['observations']), 'control_rows': len(oracle['controls']),
                                               'panels': len(public['panels']), 'predictions_computed': 0})
    inputs = pre['input_hashes'] | outputs | {'data/v35/preflight.json': sha('data/v35/preflight.json'),
                                            'data/v35/preparation_receipt.json': sha('data/v35/preparation_receipt.json')}
    write('benchmarks/adjacent_transposition_v35.json', {'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'input_hashes': inputs})
    print(json.dumps({'observations': len(public['observations']), 'control_rows': len(oracle['controls']), 'panels': len(public['panels']), 'predictions_computed': 0}))


if __name__ == '__main__': main()
