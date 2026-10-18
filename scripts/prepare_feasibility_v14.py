"""Freeze source-first acquisition and unresolved reference review without scoring."""
from datetime import datetime, timezone
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.natural_v12 import opening, utc
from fl_decipher.text import sentences
from fl_decipher.feasibility_v14 import components, unused_components, eligibility

ROOT = Path(__file__).resolve().parents[1]


def read(p):
    return json.loads(p.read_text())


def main():
    bp = ROOT/'benchmarks/kamri_feasibility_v14.json'
    assert not bp.exists(), 'Preserve frozen feasibility inputs'
    registration = ROOT/'experiments/kamri_feasibility_v14.md'
    reg_time = datetime.fromtimestamp(registration.stat().st_mtime, timezone.utc).isoformat()
    historical = {str(p.relative_to(ROOT)):read(p) for p in (ROOT/'data/normalized').glob('*.json')}
    for version in ('v12', 'v13'):
        for p in (ROOT/'data'/version/'normalized').glob('*.json'):
            historical[str(p.relative_to(ROOT))] = read(p)
    previous = read(ROOT/'benchmarks/inputs/provenance_v13_acquisition.json')
    groups = {d['source_group'] for d in historical.values()} | {r['component'] for r in previous['records']}
    inv = read(ROOT/'data/v14/inventory_components.json')
    fresh = unused_components(inv['posts'], groups, inv['prior_component_aliases'])
    assert fresh == [['religious_architecture']]
    lex = read(ROOT/'runs/000001_kamri_excerpt_baseline/lexicon.json')
    lex_groups = {g for entry in lex.values() for c in entry['candidates'] for g in c['independent_groups']}
    mentions = [p for p,d in historical.items() if 'religious architecture' in ' '.join(d['text'].lower().split())]
    assert not mentions and 'religious_architecture' not in lex_groups
    novelty = {'inventory_posts':len(inv['posts']), 'source_work_nodes':len({w for p in inv['posts'] for w in p['works']}),
        'components':components(inv['posts']), 'unused_before_v14':fresh, 'historical_groups':sorted(groups),
        'historical_document_hashes':{p:digest((ROOT/p).read_bytes()) for p in historical},
        'lexicon_groups':sorted(lex_groups), 'historical_title_mentions':mentions,
        'limits':'Public co-occurrence leads impose conservative exposure boundaries; declared persisted corpus only, not archive-wide novelty proof.'}
    dump_json(ROOT/'data/v14/component_audit.json', novelty)
    log = read(ROOT/'data/v14/discovery/search_log.json')
    review = read(ROOT/'data/v14/source_review_before_fl.json')
    fl_response = ROOT/log['fl_index_response']
    assert review['reviewed_at_utc'] < datetime.fromtimestamp(fl_response.stat().st_mtime, timezone.utc).isoformat()
    fl_raw = (ROOT/log['fl_import']).read_bytes()
    ft = opening(fl_raw.decode()); st = (ROOT/'data/v14/source_opening.txt').read_text()
    assert 0 < len(ft.split()) <= 180 and 0 < len(st.split()) <= 2000
    duplicates = [p for p,d in historical.items() if d['kind']=='fl' and any(a.text in {b.text for b in sentences(d['text'])} for a in sentences(ft) if len(a.tokens)>=8)]
    assert not duplicates
    docs = {}
    fl_receipt = snapshot(ROOT/'data/v14/raw', log['fl_url'], content=fl_raw, acquisition_kind='indexed_web_excerpt',
        locator='Exact target result from saved URL-restricted search; no current raw HTTP claim')
    src_receipt = read(ROOT/review['source_receipt'])
    src_receipt = dict(src_receipt, artifact=str(ROOT/'data/v14/acquisition/architecture_cambridge/body.bin'),
        sha256=digest((ROOT/'data/v14/acquisition/architecture_cambridge/body.bin').read_bytes()))
    for doc_id, receipt, text, kind, transforms in [
        ('fl_religious_architecture_v14',fl_receipt,ft,'fl',['Exclude title/images/navigation/off-target results','Collapse whitespace','Opening full sentences up to 180 whitespace words; no backfill or drop-cap repair']),
        ('source_religious_architecture_v14',src_receipt,st,'source',review['transformations'])]:
        doc = normalized_document(doc_id, receipt, text, kind=kind, group='religious_architecture', transformations=transforms)
        path = ROOT/'data/v14/normalized'/f'{doc_id}.json'; assert not path.exists()
        dump_json(path, doc); docs[doc_id] = {'path':str(path.relative_to(ROOT)), 'sha256':digest(path.read_bytes()), 'text_sha256':doc['text_sha256']}
    fa, sa = sentences(ft), sentences(st)
    refs = read(ROOT/'data/v14/reference_review.json')
    assert not refs['reviewed_correspondence_available'] and refs['references'] is None
    lengths = {'fl':[len(a.tokens) for a in fa], 'source':[len(a.tokens) for a in sa],
        'kind':'Pre-model diagnostic, not scoring or reference truth',
        'equal_index_equal_token_counts':sum(len(a.tokens)==len(b.tokens) for a,b in zip(fa,sa)),
        'limitation':'Count mismatch rejects direct equal-index word-position labels; does not prove non-origin or exclude edited/partial relations.'}
    tokens = [{'uid':f'religious_architecture:{i:04d}', 'atom_index':j, 'span':[t.start,t.end], 'form':t.normalized}
        for i,(j,t) in enumerate((j,t) for j,a in enumerate(fa) for t in a.tokens)]
    gate = eligibility(component_novel=True, source_prose=True, authority_verified=True, edition_verified=True,
        extraction_reviewed=True, source_scope_matches=True, fl_opening_available=True, correspondence_reviewed=False)
    cfg = {'experiment_id':'kamri_feasibility_v14', 'registration':str(registration.relative_to(ROOT)),
        'registration_sha256':digest(registration.read_bytes()), 'registration_file_mtime_utc':reg_time,
        'configuration_materialized_after_acquisition':True, 'selected_component':'religious_architecture',
        'selected_work_denominator':1, 'selected_query_denominator':1, 'source_query_limit':3, 'source_route_limit':4,
        'fl_index_query_limit':1, 'fl_page_open_limit':1, 'fl_word_cap':180, 'source_word_cap':2000,
        'model_config_if_eligible':'experiments/kamri_conflict_v11.json', 'shuffle_seed_if_eligible':14331,
        'analyst_blind':False}
    dump_json(ROOT/'experiments/kamri_feasibility_v14.json', cfg)
    receipts = sorted((ROOT/'data/v14/acquisition').glob('*/receipt.json'))
    assert len(receipts)==3 and all(reg_time < read(p)['started_at_utc'] for p in receipts)
    ledger = {'experiment_id':cfg['experiment_id'], 'stage':'source_first_feasibility',
        'status':'completed_unresolved_correspondence', 'selected_works':1, 'selected_components':1, 'selected_queries':1,
        'source_openings_acquired':1, 'fl_indexed_openings_acquired':1, 'fl_raw_openings_acquired':0,
        'reference_eligible_queries':0, 'evaluated_queries':0, 'model_executed':False, 'metrics':None,
        'new_supported_lexical_entries':0, 'semantic_gold':False,
        'records':[{'id':'religious_architecture','inventory_entry':7, 'title':'Religious Architecture: Anthropological Perspectives',
            'component':'religious_architecture','lead_provisional':True, 'gate':gate, 'references':None,
            'lexical_accuracy':None, 'controls':None, 'fl_id':'fl_religious_architecture_v14',
            'source_id':'source_religious_architecture_v14','fl_words':len(ft.split()), 'source_words':len(st.split()),
            'fl_tokens':tokens,'roster_surface_uids':[t['uid'] for t in tokens if t['form'] in ('warċa','mirnaķ','misndin')],
            'long_exact_fl_duplicate_documents':duplicates,'length_diagnostic':lengths}],
        'source_attempt_receipts':[str(p.relative_to(ROOT)) for p in receipts],
        'raw_source_requests':3, 'raw_metadata_requests':1, 'source_route_budget_used_conservatively':4,
        'exact_source_route_urls_available':3, 'source_discovery_queries':3, 'fl_index_queries':1, 'fl_page_opens':1,
        'registration_sha256':cfg['registration_sha256'], 'references_sealed_at_utc':utc(),
        'source_review_before_fl':review['reviewed_at_utc'], 'reference_review':'data/v14/reference_review.json',
        'claim_limit':'Feasibility failure to establish a reference pair in available registered openings, not a disproved source origin.',
        'remaining_unexposed_components_in_inventory_after_v14':[]}
    target = ROOT/'benchmarks/inputs/feasibility_v14_acquisition.json'; dump_json(target, ledger)
    paths = sorted(p for p in (ROOT/'data/v14').rglob('*') if p.is_file())
    paths += [registration, ROOT/'experiments/kamri_feasibility_v14.json', target,
        ROOT/'runs/000001_kamri_excerpt_baseline/lexicon.json',ROOT/'experiments/kamri_conflict_v11.json',
        ROOT/'runs/000011_kamri_anchor_conflicts/thresholds.json',ROOT/'benchmarks/inputs/provenance_v13_acquisition.json',
        ROOT/'runs/000013_kamri_source_provenance/manifest.json']
    dump_json(bp, {'schema_version':14, 'status':'frozen_source_first_feasibility_result', 'documents':docs,
        'ledger':str(target.relative_to(ROOT)), 'selected_query_denominator':1, 'reference_eligible_queries':0,
        'input_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in paths} | novelty['historical_document_hashes']})
    print('Frozen: 1 selected, 380 source words, 174 FL words, 0 reviewed reference pairs')


if __name__ == '__main__':
    main()
