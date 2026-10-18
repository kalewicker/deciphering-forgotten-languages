"""Create new versioned text views; no aligner or prediction is executed here."""
import json
from pathlib import Path
import re
from fl_decipher.corpus import snapshot,normalized_document,dump_json
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
FL={
'western_esoterism':('https://forgottenlanguages-full.forgottenlanguages.org/2018/12/daemonium-saturni-as-misre-tasdi.html', '''Ċa daċċęį mirdhi tadńam daşńaķ rakredan tawtiţ ċu kańńęį, ńo deir nalvam ċa kisnlir tadńam daşńaķ. Ńu dańtiš mirde şed ċe dańniš daċċęį daşri aš ċeaš namńdan şoaš: mişthi ċe daşddir vaşiţ, dańviġ mişthi ċe deir daşddir vaşiţ. Rakredan tawtiţ naswah datsah daċċęį konşri, ċaiš dańċaķ dańnin du daċċęį dańşlar ċe aš şi danku takwa şo kivtiġ, dańviġ misredir wanwa matdo ńi şu dańrlir aš misredir wanwa daċsiš ńi şu dańrlir, dańviġ netsaķ şi lanvam ńu lasċdir aš netsaķ ċeiš da gaşfiš ńu misre sarċe. Dagnęį, ńu esoterişar dańşlar ċe daam şa netsaķ, netvah, kivtiġ aš misre sarċe ċu naswah ńu ladċdin. Daştdar ċeaš gavşo ċu kawniš şo kitċlar. Maksu, daşfdan şi nesşnin rańki kisnlir negfiġ sanċu şo şu kifsaķ dadşi ńi vaċmah, nalńi mimse şi fasńah ‘laggdin’ aš ‘nalvi’. Agrippa kamndar şa fasńah laggdin (tafńiš ċa rańlah) aš nalvi (fatum/providentia) ńu ċoiš De occulta philosophia.'''),
'manichaean_hymn':('https://forgottenlanguages-full.forgottenlanguages.org/2018/10/lansdan-wanlah.html','''Ńo kirgam dańmanin dańċo, famtiţ mirnaķ ńi dańmadir, da şi dannlir safċedar, nakvęį aš sadwęį, ńu şu daşċiš ńi şu dańdi dańmadir, da şi mafdęį diir maşthi aš miwndar, şu dańşlar fakċenin, da minso ńu kawtdin ńu şu vandan dańldar! Ċaiš ċoiš neċte nalmadin saċde, eń natnir şu lamddar ńi gatdu aš mimfhi wa kiwdnin şu daldiġ ńi mimse, şu daşgaš şo neńviġ. Sarċaķ eń samċlir wa şu daşkam ńi nalmadin aš mimse, aš şu navne ńi dańmadir aš daċralir ńu şu daċtiš diir aš şu raşdah ńi. Ċoiš daċsiġ aš wanki raċşiġ salşi ńu aš ńu, aš eń dawtdir aš saflu şu kilgah ńi dańde kanvo. Kirshi şu kavtam migmiţ aš kiru neşmiš fagfhi daċńe, fakċnin varwdir, mimfa ve dańmdir saltiš gawmdir şu daċrlir. Da daşglar ċu şu mittam madniġ ńi şu warċa, da gańradir kiċriġ şu famtiţ dańmadir navnadin, aš vańgdin talvdar mittam vadghi ńu şu madaš ńi rakċęį, miwte daċdadir eńu daċ deir safdin ċaiš şu dadċu aš daşflir dadşi!''')}

def save(doc_id,text,receipt,group,changes):
 path=ROOT/'data/normalized'/f'{doc_id}.json'
 if path.exists():
  existing=json.loads(path.read_text())
  if existing['text'] != text:raise ValueError(f'Refusing to overwrite {path}')
  return
 dump_json(path,normalized_document(doc_id,receipt,text,kind='fl' if doc_id.startswith('fl_') else 'source',group=group,transformations=changes))

def clean(text):
 return re.sub(r'\s+',' ',text).strip()

def main():
 selections=[]
 for group,(url,text) in FL.items():
  selected=[]
  for s in sentences(text):
   if len((' '.join(selected+[s.text])).split())>180: break
   selected.append(s.text)
  text=' '.join(selected)
  receipt=snapshot(ROOT/'data/raw',url,content=text.encode(),acquisition_kind='indexed_web_excerpt',locator='Web indexed result inspected 2026-09-30; opening text, complete sentences, 180 word cap')
  save('fl_'+group,text,receipt,group,['opening indexed excerpt; cap 180 whitespace words'])
  selections.append({'group':group,'words':len(text.split()),'sentences':len(selected),'url':url})
 for group in ['gad_johnson','western_esoterism','manichaean_hymn']:
  receipt=json.loads((ROOT/'data/pdf'/f'{group}.receipt.json').read_text())
  pages=json.loads((ROOT/'data/pdf'/f'{group}.receipt.pages.json').read_text())
  changes=['pypdf text extraction; raw PDF and page text retained','collapse whitespace']
  if group=='gad_johnson':
   # Use Chapter 13 only: scope nominated before model execution.
   parts=[re.sub(r'^\s*(?:Chapter 13\s*)?\d+\s*','',p) for p in pages[37:43]]
   text=' '.join(parts)
   text=text[text.index('1Solomon'):]
   text=re.sub(r'(?<!\w)\d+(?=[A-Z“])','',text)
   text=clean(text)
   # Visually checked PDF glyphs fragmented by extraction.
   repairs={'w hoever':'whoever','l usted':'lusted','wi th':'with'}
   for before,after in repairs.items():text=text.replace(before,after)
   changes+=['PDF pages 38–43 (one-based), Chapter 13 only; remove page/chapter/verse labels',f'visually checked extraction repairs: {repairs}']
   work='gad_seer'
  elif group=='western_esoterism':
   parts=[]
   for p in pages[89:94]:
    p=re.sub(r'^Cornelius Agrippa and the five matrices\s*\d+\s*','',p)
    parts.append(p)
   text=clean(' '.join(parts)).replace('Comment: ','',1)
   # These three extraction splits are on the opening reference page.
   repairs={'of ten':'often','relig ion':'religion','th an':'than','fatu m':'fatum'}
   for before,after in repairs.items():text=text.replace(before,after)
   changes+=['PDF pages 90–94 (printed 65–69); page headers removed; opening Comment label removed',f'visually checked extraction repairs: {repairs}']
   work=group
  else:
   text=pages[21]+'\n'+pages[22]
   text=re.sub(r'196 TSUI CHI—\s*','',text)
   text=text[text.index('223 Our'):re.search(r'235 In\s+Praise',text).start()]
   text=re.sub(r'(?m)^\d+\s+','',text)
   # Keep uncertain editorial material intact; sentence splitter will expose it.
   text=clean(text)
   changes+=['PDF pages 22–23 (printed 195–196); source packet verses 223–234; verse labels/header removed; editorial parentheticals retained']
   work=group
  save('source_'+group,text,receipt,work,changes)
 dump_json(ROOT/'benchmarks/inputs/alignment_v2_acquisition.json',selections)
 for group in ['gad_johnson','western_esoterism','manichaean_hymn']:
  d=json.loads((ROOT/'data/normalized'/f'source_{group}.json').read_text())
  print('\nSOURCE',group)
  ss=sentences(d['text'],d['id'])
  for i,s in enumerate(ss):
   if group=='western_esoterism' and not ('logical' in s.text or 12<i<26):continue
   if group=='gad_johnson' and i>7:break
   if group=='manichaean_hymn' and i>9:break
   print(i,len(s.tokens),s.text)
if __name__=='__main__': main()
