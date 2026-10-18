"""Verify retained execution artifacts without rerunning or tuning models."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.experiment_v2 import validate
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'runs/000002_kamri_alignment_editions';manifest=json.loads((out/'manifest.json').read_text())
 if manifest['state']!='completed':raise ValueError('Run incomplete')
 for filename,sha in manifest['output_hashes'].items():
  assert digest((out/filename).read_bytes())==sha,filename
 # The verifier was added after execution; verify exactly the saved code set.
 for path,sha in manifest['code_hashes'].items():assert digest((ROOT/path).read_bytes())==sha,path
 for path,sha in manifest['input_hashes'].items():assert digest((ROOT/path).read_bytes())==sha,path
 benchmark=json.loads((ROOT/'benchmarks/kamri_alignment_v2.json').read_text());cfg=json.loads((ROOT/'experiments/kamri_alignment_v2.json').read_text())
 docs=validate(ROOT,benchmark,cfg);ss={k:sentences(d['text'],k) for k,d in docs.items()}
 for record in benchmark['records']:
  for source_id,edges in record['references'].items():
   for edge in edges:
    f=ss[record['fl_id']][edge['fl_index']];s=ss[source_id][edge['source_index']]
    assert edge['fl_span']==[f.start,f.end] and edge['source_span']==[s.start,s.end]
    assert docs[record['fl_id']]['text'][f.start:f.end]==f.text
    assert docs[source_id]['text'][s.start:s.end]==s.text
 report=json.loads((out/'report.json').read_text());pred=json.loads((out/'predictions.json').read_text())
 for row in report['results']:
  rankings=row['rankings'];group=row['group']
  assert len(rankings)==7
  assert len({docs[a['source_id']]['source_group'] for a in rankings})==7
  assert docs[row['source_absent']['top']['source_id']]['source_group']!=group
  assert len(row['shuffle']['strengths'])==20
  assert len(pred[group])==len(ss['fl_'+group])
 for summary in report['summaries']:
  fresh=[r for r in report['results'] if r['split']=='fresh' and r['edition']==summary['edition'] and r['method']==summary['method']]
  assert len(fresh)==summary['fresh_selected']==2
  assert summary['fresh_reference_edges']==15
  assert summary['fresh_top1']==sum(r['top_work_correct'] for r in fresh)
  assert summary['fresh_source_absent_false_admissions']==sum(r['source_absent']['false_admission'] for r in fresh)
  assert summary['fresh_retrieved_correct_edges']==sum(r['retrieved_alignment']['correct_edges'] for r in fresh)
 old=ROOT/'runs/000001_kamri_excerpt_baseline';oldmanifest=json.loads((old/'manifest.json').read_text())
 for filename,sha in oldmanifest.get('artifact_hashes',oldmanifest.get('output_hashes',{})).items():assert digest((old/filename).read_bytes())==sha,filename
 receipt={'run_id':manifest['run_id'],'state':'verified','run_manifest_sha256':digest((out/'manifest.json').read_bytes()),'elapsed_seconds':manifest['elapsed_seconds'],'checks':['run completion','all recorded input, code, and output hashes','raw acquisition artifact hashes','reviewed Unicode span locations','seven works in each candidate pool','correct work removed in absent controls','fixed fresh denominator two and reference denominator fifteen','twenty shared permutations per group','report totals recomputed','v1 retained artifact hashes'],'tests':'14 unit/synthetic tests passed before execution','new_lexical_claims':0}
 dump_json(ROOT/'reports/000002_verification.json',receipt)
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
