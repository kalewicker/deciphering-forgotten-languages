"""Freeze audit inputs; author annotations never become independent source documents."""
from pathlib import Path
import json
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text())
def main():
 raw=ROOT/'data/v15/acquisition/fake_news/body.bin'; s=BeautifulSoup(raw.read_bytes(),'html.parser')
 body=s.select_one('article#post-52112 div.entry-content.clear')
 # Only direct prose paragraphs: omit share/republish widgets and related-story embeds.
 text=' '.join(p.get_text(' ',strip=True) for p in body.find_all('p',recursive=False))
 receipt=read(raw.parent/'receipt.json')
 assert receipt['http_status']==200 and 'Denise-Marie Ordway' in s.get_text() and 'Lazer' in text
 dest=ROOT/'data/v15/normalized/source_fake_news_v15.json'; dest.parent.mkdir(exist_ok=True)
 dump_json(dest,{'id':'source_fake_news_v15','kind':'source','source_group':'models_magic',
  'source_work':'fake_news_roundup','url':receipt['requested_url'], 'text':text,
  'snapshot':{'acquisition_kind':'raw_http_attempt','http_status':200,'artifact':str(raw.relative_to(ROOT)),
    'sha256':digest(raw.read_bytes()),'acquired_at_utc':receipt['finished_at_utc']},
  'transformations':['BeautifulSoup HTML extraction','article#post-52112 div.entry-content.clear direct p children only; omit share/republish widgets and related embeds','join paragraph text with spaces'],
  'edition':'Live roundup capture 2026-10-01; original byline September 1 2017; includes later 2018 research. Not an unchanged 2017 edition.'})
 paths=sorted([*(ROOT/'data/normalized').glob('*.json'),*(ROOT/'data/v12/normalized').glob('*.json'),*(ROOT/'data/v14/normalized').glob('*.json'),dest])
 docs={}; html=['source_nichiren_images','source_dark_side_light','source_models_magic','source_fake_news_v15','source_religious_architecture_v14']
 pdf=['source_western_esoterism','source_risk_math','source_capra_foreword_v5']
 for p in paths:
  d=read(p)
  if d.get('kind') not in ('fl','source'): continue
  docid=d['id']; docs[docid]={'path':str(p.relative_to(ROOT)), 'kind':d['kind'],
    'provenance':d.get('snapshot',{}).get('acquisition_kind','unspecified'),
    'authoritative_source':docid in html+pdf,
    'extraction_review':'selected_pages_visually_reviewed' if docid in pdf else ('publisher_html_extract' if docid in html else 'qualified_or_unreviewed'),
    'source_limitation':('OCR not checked against scan' if docid=='source_christisis' else 'mirror or edition identity qualified' if d['kind']=='source' and docid not in html+pdf else 'partial persisted source selection'),
    'semantic_gold':False}
 dump_json(ROOT/'data/v15/evidence_registry.json',{'documents':docs,'pdf_qa':'data/v15/qa/review.json',
  'excluded':['v12 Scribd preview: unverified/quarantined, not independent gold','v13 publisher Juiblex excerpt: wrong scoped section','Gnosis and tradition.st PDFs: unverified mirrors; indexed route discovery only'],
  'source_routes':{'encountered':5,'raw_requests':3,'bound':12,'outcomes':{'war_accountability':'HTTP 405','second_law':'HTTP 403','fake_news':'HTTP 200','manichaean_roman_mirror':'excluded unverified mirror','secret_symbols_mirror':'excluded unverified mirror'}}})
 inputs=[ROOT/'experiments/kamri_dataset_audit_v15.md',ROOT/'data/v14/inventory_components.json',ROOT/'data/v14/component_audit.json']
 inputs+=list((ROOT/'data/v15').rglob('*'))
 for row in docs.values():
  p=ROOT/row['path']; inputs.append(p); d=read(p); artifact=d.get('snapshot',{}).get('artifact')
  if artifact: inputs.append(ROOT/artifact)
 inputs=sorted(set(p for p in inputs if p.is_file()))
 assert (ROOT/'data/v15/qa/review.json').is_file()
 dump_json(ROOT/'benchmarks/kamri_dataset_audit_v15.json',{'experiment_id':'kamri_dataset_audit_v15','stage':'reference_package_audit',
  'frozen_at_utc':utc(),'documents':docs,'input_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in inputs},
  'matching_policy':['exact','whitespace','ordered_words'],'denominator':'every numbered unit in every reading edition; combined derivative excluded',
  'eligibility_policy':'Textual matches create review leads only. No semantic training labels or new untouched evaluation folds are admitted by this audit.'})
 print('Frozen',len(inputs),'inputs;',len(docs),'independent documents')
if __name__=='__main__': main()
