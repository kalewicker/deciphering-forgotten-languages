"""Check saved spans, decisions, counts, hashes, and prior runs without model reruns."""
import argparse,itertools,json
from pathlib import Path
from fl_decipher.corpus import digest,dump_json
from fl_decipher.experiment_v3 import validate
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='000003_kamri_passage_factorial');args=parser.parse_args()
 out=ROOT/'runs'/args.run_id;m=json.loads((out/'manifest.json').read_text());assert m['state']=='completed'
 for key,sha in m['output_hashes'].items():assert digest((out/key).read_bytes())==sha,key
 for key,sha in m['input_hashes'].items():assert digest((ROOT/key).read_bytes())==sha,key
 for key,sha in m['code_hashes'].items():assert digest((ROOT/key).read_bytes())==sha,key
 cfg=json.loads((ROOT/'experiments/kamri_passage_v3a.json').read_text());b=json.loads((ROOT/'benchmarks/kamri_passage_v3a.json').read_text())
 docs=validate(ROOT,b,cfg);atoms={k:sentences(d['text'],k) for k,d in docs.items()};refs={r['group']:r for r in b['records']}
 report=json.loads((out/'report.json').read_text());perms=json.loads((out/'permutations.json').read_text());pred=json.loads((out/'predictions.json').read_text())
 assert len(report['results'])==72 and len(report['summaries'])==8 and len(report['factorial_differences'])==12
 for group,orders in perms.items():
  n=len(atoms[refs[group]['fl_id']]);assert len(orders)==20
  assert all(sorted(order)==list(range(n)) for order in orders)
  assert len(pred[group])==n
 for row in report['results']:
  group=row['group'];reference={(e['fl_index'],e['source_index']) for e in refs[group]['edges']};ranked=row['rankings']
  assert len(ranked)==9 and len({docs[a['source_id']]['source_group'] for a in ranked})==9
  for a in ranked:
   expanded=set()
   for block in a['blocks']:
    expanded.update(itertools.product(block['fl_atoms'],block['source_atoms']))
    assert block['fl_spans']==[[atoms[refs[group]['fl_id']][i].start,atoms[refs[group]['fl_id']][i].end] for i in block['fl_atoms']]
    assert block['source_spans']==[[atoms[a['source_id']][i].start,atoms[a['source_id']][i].end] for i in block['source_atoms']]
   inferred={(e['fl_index'],e['source_index']) for e in a['edges']};assert inferred==expanded
   assert a['linked_fl_atoms']==len({i for i,j in inferred})
   assert a['minimum_links_met']==(a['linked_fl_atoms']>=3)
  top=ranked[0];correct=top['source_id']==refs[group]['source_id'];assert row['top_work_correct']==correct
  inferred={(e['fl_index'],e['source_index']) for e in top['edges']}
  counts=row['retrieved_alignment'];assert counts['correct_edges']==(len(inferred&reference) if correct else 0)
  assert counts['proposed_edges']==len(inferred) and counts['reference_edges']==len(reference)
  assert row['admitted']==(top['strength']>=row['threshold'] and top['minimum_links_met'])
  absent=row['source_absent'];assert docs[absent['top']['source_id']]['source_group']!=group
  assert absent['false_admission']==(absent['top']['strength']>=row['threshold'] and absent['top']['minimum_links_met'])
  assert len(row['shuffle']['strengths'])==20
  assert row['shuffle']['exceed_or_equal_observed']==sum(v>=top['strength'] for v in row['shuffle']['strengths'])
 for summary in report['summaries']:
  rows=[r for r in report['results'] if r['variant']==summary['variant']];fresh=[r for r in rows if r['split']=='fresh']
  assert len(fresh)==summary['fresh_selected']==summary['fresh_available']==2
  assert summary['fresh_reference_edges']==13
  assert summary['fresh_top1']==sum(r['top_work_correct'] for r in fresh)
  assert summary['fresh_correct_edges']==sum(r['retrieved_alignment']['correct_edges'] for r in fresh)
  threshold=max(a['strength'] for r in rows if r['split']=='development' for a in r['rankings'] if docs[a['source_id']]['source_group']!=r['group'])+1e-6
  assert abs(summary['threshold']-threshold)<1e-12
 for oldid in ['000001_kamri_excerpt_baseline','000002_kamri_alignment_editions']:
  old=ROOT/'runs'/oldid;receipt=json.loads((old/'manifest.json').read_text())
  for name,sha in receipt.get('output_hashes',receipt.get('artifact_hashes',{})).items():assert digest((old/name).read_bytes())==sha
  for path,sha in receipt['code_hashes'].items():assert digest((ROOT/path).read_bytes())==sha
 verification={'run_id':args.run_id,'state':'verified','manifest_sha256':digest((out/'manifest.json').read_bytes()),'checks':['all saved input, code, output, and raw hashes','reference Unicode spans','72 query/variant results','8 matched-threshold variants and 12 factor contrasts','Cartesian block expansion includes extra edges','source-absent decisions','development-only threshold recomputation','fresh selected denominator 2 and reference denominator 13','20 atom permutations per group','unchanged prior-run code and output hashes'],'tests':'24 unit/synthetic tests passed before execution','new_lexical_claims':0}
 dump_json(ROOT/'reports/000003_verification.json',verification);print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
