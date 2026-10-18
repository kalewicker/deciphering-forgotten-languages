"""Independent archive/accounting/occurrence replay and preservation verification."""
from pathlib import Path
import json,re,unicodedata,zipfile
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from verify_correspondence_v6 import check_hashes
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def view(text,p):
 if p=='exact':return text
 if p=='whitespace':return ' '.join(text.split())
 return ' '.join(re.findall(r"\w+(?:['’]\w+)*",unicodedata.normalize('NFKC',text).casefold()))
def all_hits(n,h,p):
 if not n:return []
 ans=[];start=0
 while True:
  i=h.find(n,start)
  if i<0:return ans
  j=i+len(n)
  if p!='ordered_words' or ((i==0 or h[i-1]==' ') and (j==len(h) or h[j]==' ')):ans.append([i,j])
  start=i+1

def main():
 out=ROOT/'runs/000015_kamri_dataset_audit';m=check_hashes(out);b=read(ROOT/'benchmarks/kamri_dataset_audit_v15.json');r=read(out/'report.json');rows=read(out/'unit_ledger.json')['rows'];split=read(out/'split_readiness.json')
 a=read(ROOT/'data/v15/parsed_annotations.json')['articles'];inv=read(ROOT/'data/v15/archive_inventory.json')
 assert len(a)==25 and len(rows)==1026 and len({x['uid'] for x in rows})==1026
 with zipfile.ZipFile(ROOT/'data/v15/acquisition/shared_zip/body.bin') as z:
  assert len(z.infolist())==29 and set(z.namelist())=={x['name'] for x in inv['members']}
  for member in inv['members']:assert z.read(member['name'])==(ROOT/'data/v15/quarantine'/member['name']).read_bytes();assert digest(z.read(member['name']))==member['sha256']
 assert digest((ROOT/'data/v15/acquisition/shared_zip/body.bin').read_bytes())==inv['zip_sha256']
 unitmap={};count_fl=count_en=equal=0
 combined=(ROOT/'data/v15/quarantine/ALL-TRANSLATIONS.txt').read_text(encoding='utf-8-sig')
 for article in a:
  text=(ROOT/'data/v15/quarantine'/article['file']).read_text(encoding='utf-8-sig')
  assert combined.count(text.strip())==1
  # Independent label-based extraction, rather than runner's numbered-block parser.
  blocks=re.findall(r'(?m)^Kamri(?: Western)?:\s*\n(.*?)\n\s*English:\s*\n([^\n]+)',text,re.S)
  assert len(blocks)==len(article['units'])==article['claimed_unit_count']
  for (fl,en),u in zip(blocks,article['units'],strict=True):
   assert fl.strip()==u['fl'] and en.strip()==u['english'];unitmap[u['uid']]=(article,u)
   assert u['fl_words']==len(fl.split()) and u['english_words']==len(en.split())
   assert text[u['annotation_span'][0]:u['annotation_span'][1]].lstrip().startswith(str(u['number'])+'.')
   if article['language']=='Kamri':count_fl+=len(fl.split());count_en+=len(en.split());equal+=len(fl.split())==len(en.split())
 assert (count_fl,count_en,equal)==(22600,22614,654)
 assert (r['stats']['kamri_fl_whitespace_words'],r['stats']['kamri_english_whitespace_words'],r['stats']['kamri_equal_whitespace_count_units'])==(count_fl,count_en,equal)
 docs={k:read(ROOT/v['path']) for k,v in b['documents'].items()};views={k:{p:view(d['text'],p) for p in ('exact','whitespace','ordered_words')} for k,d in docs.items()}
 aliases=read(ROOT/'data/v14/inventory_components.json')['prior_component_aliases']
 for row in rows:
  article,u=unitmap[row['uid']]
  for side,key,kind in [('fl','fl_matches','fl'),('english','english_matches','source')]:
   actual={h['document_id']:h for h in row[key]};expected=set()
   for docid,d in docs.items():
    if d['kind']!=kind:continue
    for p in ('exact','whitespace','ordered_words'):
     hits=all_hits(view(u[side],p),views[docid][p],p)
     if hits:
      expected.add(docid);h=actual[docid];assert h['policy']==p and h['occurrences']==hits and h['occurrence_count']==len(hits)
      component=bool(set(aliases.get(d['source_group'],[d['source_group']])).intersection(row['component']))
      scoped=component and (side=='english' or d['url']==article['original_url'])
      assert h['scope_accepted']==scoped and h['expected_component']==component
      assert h['authoritative_source']==b['documents'][docid]['authoritative_source'];break
   assert expected==set(actual)
  ef=any(h['scope_accepted'] for h in row['fl_matches']);ee=any(h['scope_accepted'] for h in row['english_matches']);et=any(h['scope_accepted'] and h['authoritative_source'] for h in row['english_matches'])
  assert row['fl_corroborated']==ef and row['english_corroborated']==ee and row['both_corroborated']==bool(ef and ee)
  assert row['both_with_authoritative_english']==bool(ef and et)
  assert not row['semantic_gold'] and not row['semantic_training_eligible'] and not row['untouched_test_eligible']
 for key in ['english_corroborated','fl_corroborated','both_corroborated','authoritative_english_corroborated','both_with_authoritative_english','occurrence_ambiguity','short_text_requires_special_review']:
  assert r['stats'][key]==sum(x[key] for x in rows)
 for article in r['articles']:
  subset=[x for x in rows if x['article']==article['entry']]
  assert len(subset)==article['units']
  for k in ['english_corroborated','fl_corroborated','both_corroborated','both_with_authoritative_english','equal_whitespace_counts']:assert article[k]==sum(x[k] for x in subset)
 assert not split['semantic_training_eligible_uids'] and not split['untouched_test_eligible_uids']
 assert split['components']==read(ROOT/'data/v14/component_audit.json')['components'] and len(split['components'])==14
 assert split['both_textual_views_review_leads']==[x['uid'] for x in rows if x['both_corroborated']]
 assert not m['model_executed'] and not r['lexicons_used_for_induction'] and not any('LEXICON' in x['path'] for x in b['documents'].values())
 assert r['lexicon_entry_counts']=={'KAMRI-LEXICON.txt':459,'KAMRI-WESTERN-VERIFIED-LEXICON.txt':296}
 assert all(not x['same_whitespace_english'] and not x['same_ordered_english_words'] for x in read(out/'western_comparison.json'))
 body=BeautifulSoup((ROOT/'data/v15/acquisition/fake_news/body.bin').read_bytes(),'html.parser').select_one('article#post-52112 div.entry-content.clear')
 assert docs['source_fake_news_v15']['text']==' '.join(p.get_text(' ',strip=True) for p in body.find_all('p',recursive=False))
 qa=read(ROOT/'data/v15/qa/review.json');assert sum(len(x['pdf_pages_one_based']) for x in qa['records'])==14
 for x in qa['records']:assert digest((ROOT/x['raw_pdf']).read_bytes())==x['raw_sha256'];assert all((ROOT/p).is_file() for p in x['images'])
 for directory in (ROOT/'data/v15/acquisition').iterdir():
  receipt=read(directory/'receipt.json')
  for x in receipt['artifacts'].values():assert digest(Path(x['path']).read_bytes())==x['sha256'] and Path(x['path']).stat().st_size==x['bytes']
 previous=[]
 for p in sorted((ROOT/'runs').glob('0000*')):
  if p==out:continue
  check_hashes(p);previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
 assert len(previous)==14
 receipt={'state':'verified','verified_at_utc':utc(),'run_id':out.name,'manifest_sha256':digest((out/'manifest.json').read_bytes()),'stats':r['stats'],'previous_runs':previous,
  'checks':['ZIP bytes/member hashes and duplicate derivative exclusion','Independent label extraction, every unit and word denominator','Independent complete occurrence search replay, wrong component/article exclusion and every offset','Source acquisition receipts, deterministic publisher extraction and selected PDF image inventory','Fail-closed semantic eligibility and quarantined lexicons','Input/code/output hashes and fourteen historical archives preserved'],
  'limits':['Visual and source-authority judgments are single-analyst inputs, not independently reproduced semantic review.','Indexed FL snapshots and partial source copies prevent full-article gold certification.']}
 dump_json(ROOT/'reports/000015_verification.json',receipt);print(json.dumps({'state':'verified','units':len(rows),'previous_runs':len(previous)},indent=2))
if __name__=='__main__':main()
