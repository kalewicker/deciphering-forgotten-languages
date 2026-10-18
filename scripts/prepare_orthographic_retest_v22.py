"""Freeze the nineteen provenance-selected packets; no rule scoring here."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.orthographic_retest_v22 import adapt_panel

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def freeze(root=ROOT):
    pp, tp, bp = root/'data/v22/frozen_panel.json', root/'data/v22/frozen_target.json', root/'benchmarks/kamri_orthographic_retest_v22.json'
    for path in (pp, tp, bp):
        if path.exists():
            raise FileExistsError(path)
    cp = root/'experiments/kamri_orthographic_retest_v22.json'
    config = read(cp)
    for p, sha in config['input_hashes'].items():
        assert digest((root/p).read_bytes()) == sha, p
    prior_config = read(root/'experiments/kamri_orthographic_v20.json')
    assert all(config[k] == prior_config[k] for k in ['rule', 'calibration_gate', 'lure_surface', 'target_uid', 'target_gaps'])
    original = read(root/'runs/000021_kamri_calibration_evidence/future_panel.json')
    assert original['decision']['meaningfully_broader_panel_available'] and original['target_excluded']
    units = adapt_panel(original['units'], config['target_uid'])
    assert [u['uid'] for u in units] == config['calibration_uids'] and len(units) == 19
    assert sum(len(u['fl_tokens']) for u in units) == 476
    assert sum(a['component'] != b['component'] for a in units for b in units) == 274
    old_target = read(root/'data/v20/frozen_target.json')
    assert old_target['target']['uid'] == config['target_uid']
    seal_time = utc()
    dump_json(pp, {'sealed_at_utc': seal_time, 'units': units, 'target_excluded': True,
                   'origin_panel_sha256': digest((root/'runs/000021_kamri_calibration_evidence/future_panel.json').read_bytes())})
    dump_json(tp, {'sealed_at_utc': seal_time, 'target': old_target['target'], 'origin_target_sealed_at_utc': old_target['sealed_at_utc'],
                   'origin_target_sha256': digest((root/'data/v20/frozen_target.json').read_bytes())})
    hashes = config['input_hashes'] | {str(cp.relative_to(root)): digest(cp.read_bytes())}
    for path in (pp, tp):
        hashes[str(path.relative_to(root))] = digest(path.read_bytes())
    dump_json(bp, {'experiment_id': config['experiment_id'], 'frozen_at_utc': utc(), 'panel': str(pp.relative_to(root)),
                   'target': str(tp.relative_to(root)), 'input_hashes': hashes})
    print('Frozen all nineteen units and unchanged target; orthographic outcomes not scored.')

if __name__ == '__main__':
    freeze()
