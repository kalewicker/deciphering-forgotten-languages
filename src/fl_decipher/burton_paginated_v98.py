"""Page-bound literal wording test; no semantic admission or fuzzy repairs."""
import re
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Doctype
BLOCKS={'p','div','li','h1','h2','h3','h4','h5','h6','blockquote','pre','tr'}
def extract(html):
 soup=BeautifulSoup(html,'html.parser');parts=[];length=0;pages=[]
 def emit(s):
  nonlocal length
  parts.append(s);length+=len(s)
 def visit(t):
  if isinstance(t,(Comment,Doctype)):return
  if isinstance(t,NavigableString):emit(str(t));return
  if not isinstance(t,Tag) or t.name in {'script','style','noscript','template'}:return
  if 'pagenum' in t.get('class',[]):
   aa=[a for a in t.find_all(id=True) if re.fullmatch(r'Page_[0-9]+',a['id'])]
   if aa:
    assert len(aa)==1
    n=int(aa[0]['id'].split('_')[1]);assert t.get_text().strip()==f'[Pg {n}]'
    pages.append({'number':n,'text_offset':length,'label':t.get_text(),'anchor':aa[0]['id']})
   return
  if t.name=='br':emit('\n');return
  if t.name in BLOCKS:emit('\n')
  for c in t.children:visit(c)
  if t.name in BLOCKS:emit('\n')
 for t in soup.children:visit(t)
 return ''.join(parts),pages

def matches(windows,targets):
 rows=[];cursor_window=0;cursor_offset=0
 for target in targets:
  assert target
  occurrences=[]
  for i,w in enumerate(windows):
   start=0
   while (start:=w.find(target,start))>=0:
    occurrences.append({'window':i,'span':[start,start+len(target)]});start+=1
  chosen=next((o for o in occurrences if o['window']>cursor_window or o['window']==cursor_window and o['span'][0]>=cursor_offset),None)
  if chosen:cursor_window=chosen['window'];cursor_offset=chosen['span'][1]
  rows.append({'occurrences':occurrences,'ordered_occurrence':chosen})
 return {'denominator':len(targets),'matched':sum(bool(r['occurrences']) for r in rows),'ordered_matched':sum(r['ordered_occurrence'] is not None for r in rows),'rows':rows}

def assess(html,targets):
 text,pages=extract(html)
 nums=[p['number'] for p in pages];assert nums==list(range(1,352))
 offsets={p['number']:p['text_offset'] for p in pages};ranges=[[offsets[254],offsets[257]],[offsets[252],offsets[254]]]
 windows=[text[a:b] for a,b in ranges];normalize=lambda s:' '.join(s.split())
 return {'pages':pages,'extracted_text':text,'window_spans':ranges,'windows':windows,
         'normalized_windows':[normalize(w) for w in windows],
         'literal':matches(windows,targets),'whitespace':matches([normalize(w) for w in windows],[normalize(t) for t in targets])}
