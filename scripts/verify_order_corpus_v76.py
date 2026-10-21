"""Read-only reconstruction without importing E76's tokenizer or accounting."""
import hashlib
import itertools
import json
import re
import unicodedata as ud
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = 'runs/000076_order_corpus/'


def read(p):
    return json.loads((ROOT/p).read_text())


def digest(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def scan(s):
    records = []
    # Partition indexed characters into runs; strip leading combining marks.
    for valid, chars in itertools.groupby(enumerate(s), lambda x: ud.category(x[1])[0] in 'LM'):
        run = list(chars)
        if not valid:
            continue
        while run and ud.category(run[0][1])[0] != 'L':
            run.pop(0)
        if not run:
            continue
        a, b = run[0][0], run[-1][0]+1
        records.append({'start': a, 'end': b, 'form': ud.normalize('NFC', s[a:b]).casefold(),
                        'numeric_neighbor': bool((a and s[a-1].isdigit()) or (b < len(s) and s[b].isdigit()))})
    return records


def main():
    reg = read('experiments/order_corpus_v76.json')
    manifest = read(OUT+'manifest.json')
    assert manifest['state'] == 'complete'
    assert reg['registered_at_utc'] < manifest['started_at_utc'] < manifest['finished_at_utc']
    assert manifest['input_hashes'] == reg['input_hashes'] | {'experiments/order_corpus_v76.json':digest('experiments/order_corpus_v76.json')}
    for path, value in (manifest['input_hashes'] | manifest['output_hashes']).items():
        assert digest(path) == value, path
    articles = read('data/v15/parsed_annotations.json')['articles']
    old = {r['uid']:r for r in read('runs/000015_kamri_dataset_audit/unit_ledger.json')['rows']}
    bench = read('benchmarks/kamri_dataset_audit_v15.json')
    groups = read('runs/000036_mixed_edit_transfer/natural_evidence_audit.json')['connected_group_ledger']
    base = {entry:'+'.join(g['connected_components']) for g in groups for entry in g['article_entries']}
    all_groups = sorted(set(base.values()))
    mask = {t['form'] for a in articles for u in a['units'] for t in scan(u['english'])}
    assert sorted(mask) == read(OUT+'mask.json')
    ledger = read(OUT+'unit_ledger.json')
    expected_ids = [u['uid'] for a in articles for u in a['units']]
    assert [r['uid'] for r in ledger] == expected_ids
    assert set(expected_ids) == set(old) and len(expected_ids) == len(old)
    lookup = {r['uid']:r for r in ledger}
    candidates = []
    reconstructed = {}
    for a in articles:
        for u in a['units']:
            r = lookup[u['uid']]
            assert (r['article'],r['base_group'],r['language'],r['article_language']) == (a['entry'],base[a['entry']],u['language'],a['language'])
            bindings = []
            if a['language'] == u['language'] == 'Kamri':
                for hit in old[u['uid']]['fl_matches']:
                    if hit['scope_accepted'] and hit['policy'] == 'exact':
                        did = hit['document_id']; path = bench['documents'][did]['path']; doc = read(path)
                        assert doc['kind'] == 'fl' and doc['url'] == a['original_url']
                        assert hashlib.sha256(doc['text'].encode()).hexdigest() == doc['text_sha256']
                        for start,end in hit['occurrences']:
                            assert 0 <= start < end <= len(doc['text']) and doc['text'][start:end] == u['fl']
                            bindings.append({'document_id':did,'path':path,'start':start,'end':end})
            bindings.sort(key=lambda b:(b['document_id'],b['start'],b['end']))
            assert r['bindings'] == bindings
            if not bindings:
                reason = 'not_declared_kamri' if a['language'] != 'Kamri' or u['language'] != 'Kamri' else 'no_scoped_exact_fl_binding'
                assert r['exclusion'] == reason and 'tokens' not in r
                continue
            assert r['canonical_binding'] == bindings[0]
            ts = scan(u['fl'])
            for i,t in enumerate(ts):
                t['blocked'] = t['form'] in mask or t['numeric_neighbor']
                t['pair_from_previous'] = bool(i and not t['blocked'] and not ts[i-1]['blocked'] and
                    re.fullmatch(r'\s+',u['fl'][ts[i-1]['end']:t['start']]))
            assert r['tokens'] == ts
            reconstructed[r['uid']] = ts
            candidates.append(r)
    # All eight-token occurrences, then graph traversal instead of union-find.
    windows = {}
    for r in candidates:
        forms = [t['form'] for t in reconstructed[r['uid']]]
        for i in range(len(forms)-7):
            windows.setdefault(tuple(forms[i:i+8]),[]).append([r['uid'],r['base_group'],i])
    witnesses = [{'forms':list(forms),'occurrences':hits} for forms,hits in sorted(windows.items())
                 if len({h[1] for h in hits}) > 1]
    adjacency = {g:{g} for g in all_groups}
    for w in witnesses:
        members = {h[1] for h in w['occurrences']}
        for g in members:
            adjacency[g].update(members)
    mapping = {}
    for g in all_groups:
        reached = {g}; todo = [g]
        while todo:
            for other in adjacency[todo.pop()]-reached:
                reached.add(other); todo.append(other)
        mapping[g] = min(reached)
    first = {}; kept = []
    for r in sorted(candidates,key=lambda r:r['uid']):
        assert r['group'] == mapping[r['base_group']]
        forms = tuple(t['form'] for t in reconstructed[r['uid']])
        if forms in first:
            assert r['exclusion'] == 'duplicate_sequence' and r['duplicate_of'] == first[forms]
            continue
        first[forms] = r['uid']
        conflicts = sorted({prev['uid'] for prev in kept for a in prev['bindings'] for b in r['bindings']
                            if a['document_id'] == b['document_id'] and max(a['start'],b['start']) < min(a['end'],b['end'])})
        if conflicts:
            assert r['exclusion'] == 'overlapping_saved_span' and r['overlaps'] == conflicts
        else:
            assert r['exclusion'] is None
            kept.append(r)
    expected_groups = []
    for g in sorted(set(mapping.values())):
        subset = [r for r in kept if r['group'] == g]
        pairs = sum(t['pair_from_previous'] for r in subset for t in reconstructed[r['uid']])
        expected_groups.append({'group':g,'base_groups':sorted(k for k,v in mapping.items() if v == g),
            'retained_units':len(subset),'unmasked_tokens':sum(not t['blocked'] for r in subset for t in reconstructed[r['uid']]),
            'pairs':pairs,'eligible':pairs >= 100 and len(subset) >= 2})
    eligible = [g for g in expected_groups if g['eligible']]
    folds = [{'evaluation_group':g['group'],'evaluation_pairs':g['pairs'],
              'training_groups':[h['group'] for h in eligible if h != g],
              'training_pairs':sum(h['pairs'] for h in eligible if h != g)} for g in eligible]
    report = read(OUT+'report.json')
    expected = {'groups':expected_groups,'folds':folds,'duplicate_witnesses':witnesses,
                'capacity_pass':len(eligible)>=4 and all(f['training_pairs']>=500 for f in folds),
                'unit_denominator':len(ledger),'article_denominator':len(articles),
                'exact_candidate_units':len(candidates),'retained_units':len(kept),
                'eligible_groups':len(eligible),'mask_forms':len(mask),
                'model_executed':False,'semantic_benchmark_qualifying_works':0}
    assert report == expected
    print(json.dumps({'verified':True,'unit_denominator':len(ledger),'capacity_pass':report['capacity_pass'],
                      'exclusions':dict(Counter(r['exclusion'] or 'retained' for r in ledger)),
                      'model_executed':False},indent=2))


if __name__ == '__main__':
    main()
