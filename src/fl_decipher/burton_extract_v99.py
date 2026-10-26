"""Anchor-local label suppression; preserve prose in shared page containers."""
import re
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Doctype
from fl_decipher.burton_paginated_v98 import BLOCKS,matches
ANCHOR=re.compile(r'Page_([0-9]+|[ivxlcdm]+)',re.I)
LABEL=re.compile(r'^\s*(\[Pg ([^\]]+)\])')
def extract(html):
 soup=BeautifulSoup(html,'html.parser');removals={};metadata={}
 for a in soup.find_all(id=True):
  m=ANCHOR.fullmatch(a['id'])
  if not m:continue
  nxt=a.next_sibling;lab=LABEL.match(str(nxt)) if isinstance(nxt,NavigableString) and not isinstance(nxt,Comment) else None
  meta={'anchor':a['id'],'suffix':m[1],'label_status':'unlabelled','label':None}
  if lab:
   assert lab[2]==m[1],('label_mismatch',a['id'])
   assert id(nxt) not in removals
   removals[id(nxt)]=lab.span(1);meta.update(label_status='labelled',label=lab[1])
  metadata[id(a)]=meta
 pieces=[];length=0;pages=[]
 def emit(s):
  nonlocal length
  pieces.append(s);length+=len(s)
 def visit(t):
  if isinstance(t,(Comment,Doctype)):return
  if isinstance(t,NavigableString):
   s=str(t)
   if id(t) in removals:a,b=removals[id(t)];s=s[:a]+s[b:]
   emit(s);return
  if not isinstance(t,Tag) or t.name in {'script','style','noscript','template'}:return
  if id(t) in metadata:pages.append(dict(metadata[id(t)],text_offset=length))
  if t.name=='br':emit('\n');return
  if t.name in BLOCKS:emit('\n')
  for child in t.children:visit(child)
  if t.name in BLOCKS:emit('\n')
 for t in soup.children:visit(t)
 return ''.join(pieces),pages

def windows(html):
 text,pages=extract(html);numeric=[p for p in pages if p['suffix'].isdigit()]
 assert [int(p['suffix']) for p in numeric]==list(range(1,352))
 needed=[next(p for p in numeric if int(p['suffix'])==n) for n in range(252,258)]
 assert all(p['label_status']=='labelled' for p in needed)
 offsets={int(p['suffix']):p['text_offset'] for p in needed}
 assert all(offsets[n]<offsets[n+1] for n in range(252,257))
 spans=[[offsets[254],offsets[257]],[offsets[252],offsets[254]]]
 return {'extracted_text':text,'pages':pages,'window_spans':spans,'windows':[text[a:b] for a,b in spans]}

def score(ws,targets):
 normalize=lambda s:' '.join(s.split())
 return {'literal':matches(ws,targets),'whitespace':matches([normalize(w) for w in ws],[normalize(t) for t in targets]),'normalized_windows':[normalize(w) for w in ws]}
