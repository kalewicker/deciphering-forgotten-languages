"""Prepare once, then execute the registered offline capacity check once."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from fl_decipher.order_corpus_v76 import tokens, annotate, account

ROOT = Path(__file__).resolve().parents[1]
REG = 'experiments/order_corpus_v76.json'
OUT = 'runs/000076_order_corpus'
BASE = ['data/v15/parsed_annotations.json', 'runs/000015_kamri_dataset_audit/unit_ledger.json',
        'benchmarks/kamri_dataset_audit_v15.json',
        'runs/000036_mixed_edit_transfer/natural_evidence_audit.json']
CODE = ['src/fl_decipher/order_corpus_v76.py', 'scripts/order_corpus_v76.py',
        'scripts/verify_order_corpus_v76.py', 'tests/test_order_corpus_v76.py',
        'experiments/order_corpus_v76.md']


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    path = ROOT/name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def prepare():
    bench = read(BASE[2])
    paths = sorted(set(BASE + CODE + [v['path'] for v in bench['documents'].values()
                                    if read(v['path'])['kind'] == 'fl']))
    # Verify inputs already bound by the historical registration before using them.
    for path in paths:
        if path in bench['input_hashes']:
            assert sha(path) == bench['input_hashes'][path], path
    write(REG, {'experiment_id': 'order_corpus_v76', 'registered_at_utc': now(),
                'stage': 'corpus_feasibility_only', 'input_hashes': {p: sha(p) for p in paths},
                'min_groups': 4, 'min_units_per_group': 2, 'min_pairs_per_group': 100,
                'min_training_pairs_per_fold': 500, 'duplicate_window': 8,
                'model_executed': False})
    print('Frozen registration; no capacity counts computed.')


def run():
    reg = read(REG)
    for p, h in reg['input_hashes'].items():
        assert sha(p) == h, p
    out = ROOT/OUT
    out.mkdir(exist_ok=False)
    manifest = {'experiment_id': 'order_corpus_v76', 'state': 'running',
                'started_at_utc': now(), 'input_hashes': reg['input_hashes'] | {REG: sha(REG)},
                'model_executed': False}
    write(OUT+'/manifest.json', manifest)
    try:
        articles = read(BASE[0])['articles']
        old = {r['uid']: r for r in read(BASE[1])['rows']}
        bench = read(BASE[2])
        original_groups = read(BASE[3])['connected_group_ledger']
        group_articles = {}
        group_ids = []
        for g in original_groups:
            gid = '+'.join(g['connected_components'])
            group_ids.append(gid)
            for entry in g['article_entries']:
                assert entry not in group_articles
                group_articles[entry] = gid
        mask = sorted({t['form'] for a in articles for u in a['units'] for t in tokens(u['english'])})
        rows = []
        docs = {}
        for a in articles:
            for u in a['units']:
                assert u['uid'] in old
                row = {'uid': u['uid'], 'article': a['entry'], 'base_group': group_articles[a['entry']],
                       'language': u['language'], 'article_language': a['language'], 'bindings': []}
                rows.append(row)
                if a['language'] != 'Kamri' or u['language'] != 'Kamri':
                    row['exclusion'] = 'not_declared_kamri'
                    continue
                for hit in old[u['uid']]['fl_matches']:
                    if not hit['scope_accepted'] or hit['policy'] != 'exact':
                        continue
                    did = hit['document_id']
                    path = bench['documents'][did]['path']
                    if did not in docs:
                        docs[did] = read(path)
                    doc = docs[did]
                    assert doc['kind'] == 'fl' and doc['url'] == a['original_url']
                    assert hashlib.sha256(doc['text'].encode()).hexdigest() == doc['text_sha256']
                    assert set(old[u['uid']]['component']).intersection(group_articles[a['entry']].split('+'))
                    for start, end in hit['occurrences']:
                        assert 0 <= start < end <= len(doc['text'])
                        assert doc['text'][start:end] == u['fl']
                        row['bindings'].append({'document_id': did, 'path': path, 'start': start, 'end': end})
                row['bindings'].sort(key=lambda b: (b['document_id'], b['start'], b['end']))
                if not row['bindings']:
                    row['exclusion'] = 'no_scoped_exact_fl_binding'
                    continue
                row['canonical_binding'] = row['bindings'][0]
                row['tokens'] = annotate(u['fl'], set(mask))
        assert {r['uid'] for r in rows} == set(old) and len(rows) == len(old)
        candidates = [r for r in rows if r['bindings']]
        result = account(candidates, group_ids)
        result.update({'unit_denominator': len(rows), 'article_denominator': len(articles),
                       'exact_candidate_units': len(candidates),
                       'retained_units': sum(r.get('exclusion') is None for r in rows),
                       'eligible_groups': sum(g['eligible'] for g in result['groups']),
                       'mask_forms': len(mask), 'model_executed': False,
                       'semantic_benchmark_qualifying_works': 0})
        write(OUT+'/unit_ledger.json', rows)
        write(OUT+'/mask.json', mask)
        write(OUT+'/report.json', result)
        manifest.update(state='complete', finished_at_utc=now(), output_hashes={
            OUT+'/'+p: sha(OUT+'/'+p) for p in ['unit_ledger.json', 'mask.json', 'report.json']})
        print(json.dumps({k: v for k, v in result.items() if k not in ('duplicate_witnesses',)}, indent=2))
    except Exception as error:
        manifest.update(state='failed', finished_at_utc=now(), error=repr(error))
        raise
    finally:
        # Only the new run's running manifest transitions to its terminal state.
        (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.action]()
