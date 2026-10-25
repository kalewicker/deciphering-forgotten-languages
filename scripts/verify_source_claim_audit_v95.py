"""Read-only audit accounting and evidence-span checks; not a semantic reviewer."""
import json,hashlib,zipfile,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/source_claim_audit_v95.json');m=read('runs/000095_source_claim_audit/manifest.json')
 assert m['state']=='complete' and m['registration_sha256']==sha('experiments/source_claim_audit_v95.json')
 assert reg['registered_at_utc']<m['completed_at_utc'] and m['input_hashes']==reg['input_hashes']
 for mapping in [reg['input_hashes'],m['output_and_audit_code_hashes']]:
  for p,h in mapping.items():assert sha(p)==h,p
 ledger=read('runs/000092_yid_adapter/ledger.json');records=read('data/v95/assessments.json');selected=read('data/v95/selected_claims.json')
 with zipfile.ZipFile(ROOT/'data/v90/acquisition/hop_01/body.bin') as z:text=z.read(ledger['source_member']).decode('utf-8')
 expected=[];roles=locators=passages=0
 assert [x['number'] for x in selected]==[1,43,86]
 for entry in selected:
  row=next(r for r in ledger['sources']['rows'] if r['number']==entry['number'])
  assert entry['row']==row and entry['text']==text[slice(*row['span'])]
  for i,c in enumerate(row['claims'],1):
   key=(entry['number'],i);expected.append(key)
   rs=[r for r in records if (r['candidate'],r['claim_ordinal'])==key];assert len(rs)==1;r=rs[0]
   assert r['claim_span']==c['span']
   for e in r['evidence']:
    a,b=e['span'];assert c['span'][0]<=a<=b<=c['span'][1] and text[a:b]==e['text']
   assert r['evidence'][0]['span']==c['citation_span']
   assert r['evidence'][1:]==[{'field':f['key'],'span':f['value_span'],'text':f['value']} for f in c['fields']]
   rr=[e for e in r['evidence'] if e['field']=='Role'];uu=[e for e in r['evidence'] if e['field']=='URL']
   assert len(rr)==r['role_field_count'];roles+=bool(rr);locators+=bool(uu)
   printed=any(re.search(r'printed pages [0-9]+-[0-9]+',e['text']) for e in rr)
   assert printed==r['location_is_external_passage'];passages+=printed
   assert r['source_accessibility']=='untried' and not r['source_content_verified']
 assert len(records)==len(expected)==8 and len(set(expected))==8
 report=read('runs/000095_source_claim_audit/report.json')
 assert report['claims_per_post']=={'1':2,'43':5,'86':1}
 assert report['claims_with_role_field']==roles==7 and report['claims_with_citation_and_locator']==locators==8
 assert report['claims_with_explicit_external_passage_location']==passages==1
 assert all(not r['explicit_package_ordinal_to_source_span_mapping'] for r in records)
 assert report['sources_verified']==report['network_requests']==0
 print(json.dumps({'verified':True,'posts':3,'claims':8,'evidence_spans':sum(len(r['evidence']) for r in records),'manual_assessment_not_independently_adjudicated':True,'verifier_written_after_audit':True},indent=2))
if __name__=='__main__':main()
