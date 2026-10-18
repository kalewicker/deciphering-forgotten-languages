"""Seal offline acquisition observations; never fetches or invokes the scorer."""
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest, dump_json
from fl_decipher.experiment_v7 import read
from fl_decipher.natural_v12 import utc
from fl_decipher.provenance_v13 import provenance_gate, validate_budget, validate_result

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT/'benchmarks/inputs/provenance_v13_acquisition.json'
    assert not target.exists(), 'Preserve the frozen ledger; no replacement'
    log = read(ROOT/'data/v13/discovery/search_log.json')
    receipt_paths = sorted((ROOT/'data/v13/acquisition').glob('*/receipt.json'))
    receipts = [read(p) for p in receipt_paths]
    validate_budget(log, receipts)
    old = read(ROOT/'benchmarks/inputs/natural_v12_acquisition.json')
    old_b = read(ROOT/'benchmarks/kamri_natural_v12.json')
    registration = ROOT/'experiments/kamri_provenance_v13.md'
    reg_time = datetime.fromtimestamp(registration.stat().st_mtime, timezone.utc).isoformat()
    assert all(reg_time < r['started_at_utc'] for r in receipts)
    body = ROOT/'data/v13/acquisition/vile_library_capture/body.bin'
    visible = BeautifulSoup(body.read_bytes(), 'html.parser').get_text('\n', strip=True)
    visible_path = ROOT/'data/v13/vile_capture_visible.txt'
    assert visible_path.read_text() == visible
    assert 'Book of Vile Darkness\nby Monte Cook' in visible and '12/06/2002' in visible
    assert 'Juiblex, the Faceless Lord' in visible and 'Defining Evil' not in visible
    capture = read(body.parent/'receipt.json')
    assert capture['http_status'] == 200 and 'archive.wizards.com/default.asp?x=dnd/ex/20021206' in capture['final_url']
    assessment = {
        'source_id': 'vile_darkness_publisher_excerpt_v13', 'title': 'Book of Vile Darkness',
        'author': 'Monte Cook', 'publisher': 'Wizards of the Coast', 'page_date': '2002-12-06',
        'edition_assessment': 'Author and contemporary publisher page date support the 2002 edition; not the later 2011 edition.',
        'capture_requested_url': capture['requested_url'], 'capture_final_url': capture['final_url'],
        'capture_timestamp_from_final_url': '20161101210131',
        'receipt': str((body.parent/'receipt.json').relative_to(ROOT)),
        'diagnostic_extraction': str(visible_path.relative_to(ROOT)),
        'transformations': ["BeautifulSoup html.parser; get_text('\\n', strip=True); no OCR or drop-cap repair"],
        'available_section': 'Juiblex, the Faceless Lord; includes stat block and later related subsections',
        'registered_section': 'Chapter 1 opening, up to 2000 complete-sentence words',
        'reference_eligible': False, 'used_for_predictions': False,
        'reason': 'Publisher provenance is supported, but this excerpt is a different section. Full-page diagnostic text is excluded from the scoped source corpus and references.',
    }
    dump_json(ROOT/'data/v13/publisher_excerpt_assessment.json', assessment)
    records = []
    for r in old['records']:
        row = {k:r[k] for k in ('id', 'title', 'component', 'fl_url', 'fl_id', 'source_scope', 'fl_whitespace_words', 'fl_atom_count', 'roster_surface_uids')}
        row.update(selected_token_count=len(r['fl_tokens']), previous_acquisition_status=r['acquisition_status'],
                   references=None, lexical_accuracy=None, controls=None, semantic_gold=False)
        authority = r['id'] == 'vile_darkness'
        row['gate'] = provenance_gate(source_prose=authority, authority_verified=authority,
            edition_verified=authority, source_scope_matches=False, extraction_reviewed=authority,
            passage_reviewed=False, component_novel=r['gate']['requirements']['component_novel'])
        if authority:
            row.update(acquisition_status='verified_publisher_excerpt_wrong_section',
                reason='Archived 2002 publisher excerpt by Monte Cook is inspectable but covers Juiblex, not the frozen chapter-one opening. Retailer routes returned HTTP 403; the publisher URL redirects to the current corporate home page.',
                authority_assessment='data/v13/publisher_excerpt_assessment.json')
        else:
            row.update(acquisition_status='author_lead_unresolved_no_source_prose',
                reason='Diane Vera primary profile and March 2010 blog do not identify or contain Liber Azazel. Dedication is not authorship. Linked www site and Church of Azazel endpoint fail DNS; one external diagnostic repeats the same www failure.',
                authority_assessment=None)
        records.append(row)
    cfg = {'experiment_id':'kamri_provenance_v13', 'registration':str(registration.relative_to(ROOT)),
        'registration_sha256':digest(registration.read_bytes()), 'registration_file_mtime_utc':reg_time,
        'configuration_materialized_after_acquisition':True, 'previous_run':'000012_kamri_natural_acquisition',
        'discovery_queries_per_work':4, 'source_routes_per_work':4, 'shuffle_seed_if_eligible':13331,
        'frozen_model_config':'experiments/kamri_conflict_v11.json',
        'frozen_lexicon':'runs/000001_kamri_excerpt_baseline/lexicon.json',
        'frozen_thresholds':'runs/000011_kamri_anchor_conflicts/thresholds.json',
        'analyst_blind':False, 'no_new_fl_selection':True}
    dump_json(ROOT/'experiments/kamri_provenance_v13.json', cfg)
    ledger = {'experiment_id':cfg['experiment_id'], 'stage':'source_provenance_eligibility',
        'status':'completed_no_reference_eligible_pairs', 'selected_works':2, 'selected_queries':2,
        'selected_components':2, 'reference_eligible_queries':0, 'evaluated_queries':0,
        'model_executed':False, 'metrics':None, 'new_supported_lexical_entries':0,
        'inspectable_publisher_work_excerpts':1, 'eligible_scoped_source_packets':0,
        'records':records, 'source_attempt_receipts':[str(p.relative_to(ROOT)) for p in receipt_paths],
        'raw_requests':9, 'distinct_source_routes':8, 'discovery_queries':8,
        'registration_sha256':cfg['registration_sha256'], 'references_sealed_at_utc':utc(),
        'discovery_logging_limit':'First two search responses and follow-up route tool responses retained. Third query batch (two retailer searches, both empty) logged from the observed tool output; its combined profile open was not separately serialized. Raw profile HTML is retained.',
        'negative_disposition':'No registered controls or permutations generated: zero eligible queries, no model call.',
        'previous_outcome_preserved':old['status']}
    validate_result(ledger, old); dump_json(target, ledger)
    inputs = sorted(p for p in (ROOT/'data/v13').rglob('*') if p.is_file())
    inputs += [target, ROOT/'experiments/kamri_provenance_v13.json', registration,
        ROOT/'benchmarks/inputs/natural_v12_acquisition.json', ROOT/'benchmarks/inputs/natural_v12_novelty.json',
        ROOT/'benchmarks/kamri_natural_v12.json', ROOT/cfg['frozen_model_config'], ROOT/cfg['frozen_lexicon'],
        ROOT/cfg['frozen_thresholds'], ROOT/'runs/000012_kamri_natural_acquisition/manifest.json',
        *[ROOT/v['path'] for v in old_b['documents'].values()]]
    bench = {'schema_version':13, 'status':'frozen_source_provenance_result',
        'ledger':str(target.relative_to(ROOT)), 'documents':old_b['documents'],
        'selected_query_denominator':2, 'reference_eligible_queries':0, 'model_executed':False,
        'input_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in inputs}}
    dump_json(ROOT/'benchmarks/kamri_provenance_v13.json', bench)
    print('Sealed: 2 selected, 1 verified work excerpt, 0 scoped references, 0 evaluated')


if __name__ == '__main__':
    main()
