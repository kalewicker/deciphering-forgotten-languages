"""One-shot recording of disclosed manual catalog assessments, not source validation."""
import json,hashlib,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,x):
 with (ROOT/p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
# Assessments were authored after the registered, fixed catalog inspection.
ASSESSMENTS={
 (1,1):('exact_local_parallel','heading identified as S002; correspondence to package ordinal not supplied','encoded heading S002','native_post',False),
 (1,2):('claimed_exact_source_lock','all 22 encoded prose units; first pages 254-256, then 252-253','printed pages 254-256 then 252-253','external_source',True),
 (43,1):('claimed_ordered_primary_source','34 of 36 encoded units; no unit IDs or ordinal subset supplied',None,'external_source',False),
 (43,2):('contextual_source_claim','title frame and named object-analysis context; not a unit range',None,'external_source',False),
 (43,3):('embedded_english_quotation_source','embedded English quotation; no opaque-unit scope specified',None,'external_source',False),
 (43,4):('contextual_decoding_claim','site-authored question bridge constrained by adjacent passages; no ordinal supplied',None,'native_post',False),
 (43,5):('contextual_decoding_claim','site-authored one-word answer constrained by punctuation and quotation; no ordinal supplied',None,'native_post',False),
 (86,1):('citation_only_unspecified_relationship','no Role field or coverage statement',None,'external_source',False),
}
def main():
 reg=read('experiments/source_claim_audit_v95.json')
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 selected=read('data/v95/selected_claims.json');ledger=read('runs/000092_yid_adapter/ledger.json')
 with zipfile.ZipFile(ROOT/'data/v90/acquisition/hop_01/body.bin') as z:raw=z.read(ledger['source_member']);text=raw.decode('utf-8')
 prior=read('runs/000091_yid_schema/member_ledger.json');assert hashlib.sha256(raw).hexdigest()==next(e['sha256'] for e in prior if e['name']==ledger['source_member'])
 records=[]
 for entry in selected:
  n=entry['number'];r=entry['row'];assert r==next(r for r in ledger['sources']['rows'] if r['number']==n)
  assert entry['text']==text[slice(*r['span'])]
  for i,c in enumerate(r['claims'],1):
   relation,scope,location,kind,testable=ASSESSMENTS[(n,i)]
   roles=[f for f in c['fields'] if f['key']=='Role'];urls=[f for f in c['fields'] if f['key']=='URL']
   evidence=[{'field':'citation','span':c['citation_span'],'text':text[slice(*c['citation_span'])]}]
   evidence += [{'field':f['key'],'span':f['value_span'],'text':f['value']} for f in c['fields']]
   assert all(text[slice(*e['span'])]==e['text'] for e in evidence)
   records.append({'candidate':n,'claim_ordinal':i,'claim_span':c['span'],'evidence':evidence,
    'cited_item_present':bool(text[slice(*c['citation_span'])]),'literal_locator_present':bool(urls),
    'role_field_count':len(roles),'relationship_assessment':relation,'declared_coverage_assessment':scope,
    'passage_location_as_claimed':location,'location_is_external_passage':testable,
    'locator_role':kind,'explicit_package_ordinal_to_source_span_mapping':False,
    'source_accessibility':'untried','source_content_verified':False,'semantic_validity':'unvalidated'})
 assert len(records)==len(ASSESSMENTS)==8
 out=ROOT/'runs/000095_source_claim_audit';out.mkdir(exist_ok=False)
 write('data/v95/assessments.json',records)
 report={'candidate_numbers':[1,43,86],'posts':3,'claim_records':8,'claims_per_post':{str(n):sum(r['candidate']==n for r in records) for n in [1,43,86]},
  'claims_with_citation_and_locator':sum(r['cited_item_present'] and r['literal_locator_present'] for r in records),
  'claims_with_role_field':sum(r['role_field_count']>0 for r in records),'claims_with_explicit_external_passage_location':sum(r['location_is_external_passage'] for r in records),
  'claims_with_explicit_package_ordinal_to_source_span_mapping':0,'recommended_next_claim':{'candidate':1,'claim_ordinal':2,'reason':'explicit printed page ranges and stated prose coverage; retrieval feasibility remains untried'},
  'network_requests':0,'sources_verified':0,'semantic_benchmark_qualifying_works':0,'new_confirmation_units':0}
 write('runs/000095_source_claim_audit/report.json',report)
 paths=['data/v95/selected_claims.json','data/v95/assessments.json','runs/000095_source_claim_audit/report.json','scripts/source_claim_audit_v95.py']
 write('runs/000095_source_claim_audit/manifest.json',{'state':'complete','completed_at_utc':datetime.now(timezone.utc).isoformat(),'registration_sha256':sha('experiments/source_claim_audit_v95.json'),'input_hashes':reg['input_hashes'],'output_and_audit_code_hashes':{p:sha(p) for p in paths},'manual_assessment_authored_after_inspection':True})
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
