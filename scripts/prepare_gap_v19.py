"""One-shot evidence preparation after registration, before gap scoring."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.gap_v19 import gap_gate

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())

def prepare(root=ROOT):
    evidence_path = root/'data/v19/frozen_evidence.json'
    benchmark_path = root/'benchmarks/kamri_gap_v19.json'
    # Guard ALL outputs before changing any of them, including partial previous preparation.
    for path in (evidence_path, benchmark_path):
        if path.exists():
            raise FileExistsError(path)
    config_path = root/'experiments/kamri_gap_v19.json'
    config = read(config_path)
    for path, sha in config['input_hashes'].items():
        assert digest((root/path).read_bytes()) == sha, path
    uid = config['unit_uid']
    prediction = next(u for u in read(root/'data/v18/frozen_predictions.json')['units'] if u['uid'] == uid)
    reference = next(u for u in read(root/'data/v18/frozen_references.json')['units'] if u['uid'] == uid)
    target = next(u for u in read(root/'data/v18/targets.json')['units'] if u['uid'] == uid)
    assert reference['gate']['unmet'] == ['equal_token_counts']
    gate = gap_gate(reference, len(prediction['tokens']), len(reference['source_tokens']))
    assert gate['development_gap_score_eligible']
    evidence = {'sealed_at_utc': utc(), 'uid': uid, 'prediction': prediction,
                'reference': reference, 'target': target, 'gap_gate': gate,
                'original_v18_gate': reference['gate'], 'semantic_gold': False,
                'current_raw_fl': False, 'new_predictions_executed': False}
    hashes = config['input_hashes'] | {str(config_path.relative_to(root)): digest(config_path.read_bytes())}
    dump_json(evidence_path, evidence)
    hashes[str(evidence_path.relative_to(root))] = digest(evidence_path.read_bytes())
    benchmark = {'experiment_id': config['experiment_id'], 'frozen_at_utc': utc(),
                 'evidence': str(evidence_path.relative_to(root)), 'input_hashes': hashes}
    dump_json(benchmark_path, benchmark)
    print('Frozen original 21/22-token evidence; v18 equal-length failure preserved.')

if __name__ == '__main__':
    prepare()
