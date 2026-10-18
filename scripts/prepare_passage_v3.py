"""Prepare fixed new sources and indexed FL samples, without model execution."""
import json,re
from pathlib import Path
from fl_decipher.corpus import dump_json,normalized_document,snapshot,html_text
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
INPUTS={
'risk_math':('https://forgottenlanguages-full.forgottenlanguages.org/2019/05/war-algorithmics-quantum-game-theory.html','''Newgdir lalnin daşviţ du fagniš salwu şo magęį şa daċċęį dańde kilnlir mivmhi ńu gaşflar savdam dańllar kiggdir aš ńu kigvah aš laċglir utunlir kaċtam. Daċċęį neşmam kikşiš datrlar ńi newgdir lalnin daşviţ ragknin ratle kaċtam walmiš masmah şu darmah ńi laċglir kagċi aš laċglir valda nadgdir. Şu dańde kilnlir mivmhi ńi newgdir lalnin daşviţ şa newgdir ekonofisicir natnir şa şu mivsdan ńi dańvlar datrlir ńi newgdir lalnin daşviţ, ńu neşlu, ńu davlu daştdar şoaš daşńdar daşkęį aš tagmdin takgiš. Newgdir lalnin daşviţ lańńiš dadşu ńu nanmaķ kinriš kiggdir ńi daċmo dagsiġ tasmlar, de şu nesşlar takdam dańraš daċla şa şu daşto neşwa daċsiš newgdir gatwiţ aš ranwir ċa şu sanddan kirwdan rakgiġ daştam ve mingdin daşto şa ċeaš kinfnin.'''),
'models_magic':('https://forgottenlanguages-full.forgottenlanguages.org/2019/09/misinfons-and-hypermemetic-logic.html','''Şu mavsdin nadgah ńańi hipermemetik mirde şi fakċnin kavrlir daċċęįš vaċddin şi tafliġ gawvhi kamsam doaš şu kiċfa mişthi sakge vamda tatċlir. Ċeaš valtiš faffaķ nerşdir şo kamda ċu tawwdan kimgam şoaš talsiţ şi kifwiġ, savċiš mişthi namńęį mavsdin ċu walfu şo kiştu (vaċnir ċeiš fafvam savċiš gańńah milfiġ ńańi nalmdin navńaķ kiċfęį gaslir) daċċęįš tawwdan mavsdin kidċdan deir mańvdin mivgnin navńaķ kimgam. Vańgdin, mişthi şi kivsiţ diir mimviţ daċċęįš deir fasdlar ńu şu ranve ńańi sawo vańsi kaċwah. Mişthi ċeiš vaċdiš fafvam vaftaķ navńaķ tatmir şi damşaķ ńi daċċęį deiš daċċęįš şi damşaķ ńi daċċęį nekru. Ńu darlir mişthi mivvdir fafvam minċdar şo newgdir negfam rańki diir rakiţ mivgnin kimgam. Mişthi ċeiš, maksu, faċshi mişwah şo daċċęį miwgęį ńiir an navko navńaķ di navvo miwnam tagńu kavta.''')}

def save(doc_id,text,receipt,group,changes):
 path=ROOT/'data/normalized'/f'{doc_id}.json'
 if path.exists():
  if json.loads(path.read_text())['text']!=text:raise ValueError('Refusing to change an existing input')
  return
 dump_json(path,normalized_document(doc_id,receipt,text,kind='fl' if doc_id.startswith('fl_') else 'source',group=group,transformations=changes))

def main():
 ledger=[]
 for group,(url,text) in INPUTS.items():
  selected=[]
  for s in sentences(text):
   if len(' '.join(selected+[s.text]).split())>180:break
   selected.append(s.text)
  text=' '.join(selected)
  receipt=snapshot(ROOT/'data/raw',url,content=text.encode(),acquisition_kind='indexed_web_excerpt',locator='Indexed web result inspected 2026-09-30; first Kamri block after title/English opening quote; no raw-page claim')
  save('fl_'+group,text,receipt,group,['opening Kamri block; complete sentences; 180 whitespace-word cap; retain alternate register'])
  ledger.append({'group':group,'status':'available','words':len(text.split()),'sentences':len(selected),'url':url})
  receipt=json.loads((ROOT/'data/v3'/f'{group}.receipt.json').read_text())
  if group=='models_magic':
   text=html_text(Path(receipt['artifact']).read_bytes(),'.td-post-content')
   text=text[:text.index('UBIQUE DAEMON')].strip()
   changes=['HTML article body selector .td-post-content; remove headings/superscripts by existing extractor','stop before closing motto/author promo and share widgets','collapse whitespace; numbered list prose retained']
  else:
   pages=json.loads((ROOT/'data/v3/risk_math.plumber_pages.json').read_text())
   parts=[]
   for page in pages:
    page=re.sub(r'(?m)^.*(?:arXiv:|\[physics\.soc-ph\]).*$','',page)
    page=re.sub(r'(?m)^\d+ (?:Introduction|Quantum Game Theory|Risk Mathematics, Quantum Games and Quantum Risk Structures)(?: \d+)?\s*$','',page)
    page=re.sub(r'(?m)^\d+\s*$','',page)
    page=re.sub(r'\[\d+(?:\s*,\s*\d+)*\]','',page)
    page=re.sub(r'(?<=[A-Za-z])\d+(?=\s|\[)','',page)
    page=re.sub(r'(?<=\w)-\s*\n\s*(?=\w)','',page)
    parts.append(page)
   text=re.sub(r'\s+',' ',' '.join(parts)).strip()
   changes=['pdfplumber x_tolerance=2 y_tolerance=3; PDF pages 1–3; raw/page extraction retained','remove running/section headers, standalone page numbers, arXiv identifier line, numeric bracket references, attached numeric footnote markers','join line-wrap hyphens; collapse whitespace; footnote prose retained','opening matched paragraph visually checked against PDF page 2; no paraphrase corrections']
  save('source_'+group,text,receipt,group,changes)
 dump_json(ROOT/'benchmarks/inputs/passage_v3_acquisition.json',ledger)
 for group in INPUTS:
  print('\n',group)
  fl=json.loads((ROOT/'data/normalized'/f'fl_{group}.json').read_text());en=json.loads((ROOT/'data/normalized'/f'source_{group}.json').read_text())
  print('FL',len(fl['text'].split()),len(sentences(fl['text'])))
  for i,s in enumerate(sentences(en['text'])):
   if ('Quantum game theory has' in s.text or 'particularly effective' in s.text or 'good empirical matching of quantum' in s.text or 'theory fits well' in s.text or 'information model of magic is' in s.text or 60<=i<=75):print(i,len(s.tokens),s.text)
if __name__=='__main__':main()
