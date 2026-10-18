"""Freeze complete prior development pairs and both unchanged target hypotheses."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())

def statement_tokens(uid, document, statement):
    return [{'unit_uid': uid, 'document': document, 'index': i, 'surface': t.surface,
             'form': t.normalized, 'span': [t.start, t.end], 'view_surface': t.surface}
            for i, t in enumerate(tokens(statement['text'], statement['span'][0]))]


def freeze(root=ROOT):
    panel_path, target_path, benchmark_path = (root/'data/v20/frozen_panel.json', root/'data/v20/frozen_target.json', root/'benchmarks/kamri_orthographic_v20.json')
    for path in (panel_path, target_path, benchmark_path):
        if path.exists():
            raise FileExistsError(path)
    cp = root/'experiments/kamri_orthographic_v20.json'
    config = read(cp)
    for path, sha in config['input_hashes'].items():
        assert digest((root/path).read_bytes()) == sha, path
    v16 = {u['uid']: u for u in read(root/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units']}
    v18 = {u['uid']: u for u in read(root/'data/v18/frozen_references.json')['units']}
    panel = []
    for uid in config['calibration_uids']:
        if uid in v16:
            u = v16[uid]
            assert u['independent_complete_statement_pair'] and u['equal_project_token_counts']
            fl, source = u['fl_statement_matches'][0], u['english_statement_matches'][0]
            g = u['component']
            fd, sd = f'data/v16/normalized/{g}_fl.json', f'data/v16/normalized/{g}_source.json'
            origin = 'runs/000016_kamri_correspondence_review/unit_ledger.json'
            old_gate = {'independent_complete_statement_pair': u['independent_complete_statement_pair'], 'equal_project_token_counts': u['equal_project_token_counts']}
        else:
            u = v18[uid]
            assert u['gate']['development_positional_score_eligible']
            fl = u['historical_fl_statement_matches'][0]
            source = {'text': u['source_statement'], 'span': u['source_span'], 'block_id': u['source_block_id']}
            g, fd, sd = u['component'], u['fl_document'], u['source_document']
            origin, old_gate = 'data/v18/frozen_references.json', u['gate']
        assert read(root/sd)['source_authority_reviewed']
        assert read(root/fd)['snapshot']['acquisition_kind'] == 'indexed_web_excerpt'
        for document, statement in [(fd, fl), (sd, source)]:
            assert read(root/document)['text'][slice(*statement['span'])] == statement['text']
        ft, et = statement_tokens(uid, fd, fl), statement_tokens(uid, sd, source)
        assert len(ft) == len(et)
        panel.append({'uid': uid, 'component': g, 'origin': origin, 'original_gate': old_gate,
                      'fl_statement': fl, 'source_statement': source, 'fl_document': fd, 'source_document': sd,
                      'fl_tokens': ft, 'source_tokens': et, 'current_raw_fl': False,
                      'semantic_gold': False, 'untouched_test_eligible': False})
    assert len(panel) == config['unit_denominator'] == 11 and config['target_uid'] not in config['calibration_uids']
    old = read(root/'data/v19/frozen_evidence.json')
    ref = old['reference']
    uid = config['target_uid']
    assert old['uid'] == uid
    fl = ref['historical_fl_statement_matches'][0]
    source = {'text': ref['source_statement'], 'span': ref['source_span'], 'block_id': ref['source_block_id']}
    all_alignments = read(root/'runs/000019_kamri_single_gap/observed_alignments.json')
    assert all_alignments['maxima']['secondary']['gaps'] == all_alignments['maximizer_intersection'] == config['target_gaps'] == [1, 2]
    target = {'uid': uid, 'component': ref['component'], 'fl_document': ref['fl_document'], 'source_document': ref['source_document'],
              'fl_statement': fl, 'source_statement': source,
              'fl_tokens': statement_tokens(uid, ref['fl_document'], fl), 'source_tokens': statement_tokens(uid, ref['source_document'], source),
              'gap_gate': old['gap_gate'], 'original_v18_gate': old['original_v18_gate'],
              'alignments': [a for a in all_alignments['alignments'] if a['gap'] in config['target_gaps']],
              'current_raw_fl': False, 'semantic_gold': False, 'untouched_test_eligible': False}
    seal_time = utc()
    dump_json(panel_path, {'sealed_at_utc': seal_time, 'units': panel, 'target_excluded': True})
    dump_json(target_path, {'sealed_at_utc': seal_time, 'target': target})
    hashes = config['input_hashes'] | {str(cp.relative_to(root)): digest(cp.read_bytes())}
    for path in (panel_path, target_path):
        hashes[str(path.relative_to(root))] = digest(path.read_bytes())
    dump_json(benchmark_path, {'experiment_id': config['experiment_id'], 'frozen_at_utc': utc(),
                              'panel': str(panel_path.relative_to(root)), 'target': str(target_path.relative_to(root)), 'input_hashes': hashes})
    print('Frozen all eleven calibration units and both original target hypotheses; no orthographic scores computed.')

if __name__ == '__main__':
    freeze()
