"""Execute the frozen zero-network E65 recovery once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.textual_references_v65 import recover

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/textual_references_v65.json'
RUN='runs/000065_textual_references'
CODE=['src/fl_decipher/textual_references_v65.py','scripts/textual_references_v65.py','tests/test_textual_references_v65.py']
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,o):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(o,f,indent=2,ensure_ascii=False);f.write('\n')


def main():
    cfg=read(CFG)
    assert not (ROOT/'data/v65').exists() and not (ROOT/RUN).exists()
    assert cfg['network_request_budget']==cfg['source_selection_budget']==0
    for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
    write('data/v65/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]}})
    assert read('data/v64/admission_decision.json')['limited_admission'] is True
    assert read('data/v63/target_gate.json')['passed'] is False
    result=recover((ROOT/cfg['raw']).read_bytes(),read(cfg['export']),read(cfg['known_exposure'])['urls'])
    write('data/v65/reference_inventory.json',result)
    occurrences=result['identifier_occurrences'];refs=result['references']
    report={'experiment_id':'textual_references_v65','development_recovery_after_preparatory_exposure':True,
        'material_denominator':1,'body_characters':result['unicode_characters'],'included_text_leaves':len(result['leaves']),
        'nonempty_owner_runs':len(result['runs']),'boundary_matches':len(result['boundary_match_run_ids']),'tail_status':result['tail_status'],
        'reference_rows':len(refs),'reference_rows_with_recognized_identifier':sum(r['resolution_status']=='identifier_syntax_recovered_metadata_unverified' for r in refs),
        'reference_rows_without_recognized_identifier':sum(r['resolution_status']=='no_recognized_direct_identifier' for r in refs),
        'identifier_occurrences':len(occurrences),'malformed_or_cross_run_occurrences':sum(r['identifier'] is None for r in occurrences),
        'recognized_identifiers':result['recognized_identifiers'],'known_identifier_matches':result['known_identifier_matches'],
        'research_network_requests':0,'source_candidates_selected':0,'source_requests':0,'alignment_or_lexical_scores':0,
        'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'semantic_or_source_identity_admissions':0,'natural_benchmark_capacity_met':False,'anita_route_reopened':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False}
    write(RUN+'/report.json',report)
    write(RUN+'/manifest.json',{'experiment_id':'textual_references_v65','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in ['data/v65/preflight.json','data/v65/reference_inventory.json']},
        'verifier_written_after_recovery':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
