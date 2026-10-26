"""Separate stack-based extraction and label check; no production extractor import."""
import re
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Doctype

def replay(html):
 soup=BeautifulSoup(html,'html.parser');stack=[(soup,False)];output=[];offset=0;pages=[];skip={}
 def emit(s):
  nonlocal offset
  output.append(s);offset+=len(s)
 while stack:
  t,exit_node=stack.pop()
  if isinstance(t,(Comment,Doctype)):continue
  if isinstance(t,NavigableString):
   s=str(t)
   if id(t) in skip:
    left,right=skip[id(t)];s=s[:left]+s[right:]
   emit(s);continue
  if not isinstance(t,Tag) or t.name in ('script','style','noscript','template'):continue
  if not exit_node:
   match=re.fullmatch(r'Page_([0-9]+|[ivxlcdm]+)',t.get('id',''),re.I)
   if match:
    suffix=match[1];nxt=t.next_sibling;label=None
    if isinstance(nxt,NavigableString) and not isinstance(nxt,Comment):
     content=str(nxt);left=len(content)-len(content.lstrip())
     if content[left:].startswith('[Pg '):
      end=content.find(']',left)
      if end>=0:
       label=content[left:end+1];assert label==f'[Pg {suffix}]'
       assert id(nxt) not in skip;skip[id(nxt)]=(left,end+1)
    pages.append({'anchor':t['id'],'suffix':suffix,'label_status':'labelled' if label else 'unlabelled','label':label,'text_offset':offset})
  if t.name=='br':emit('\n');continue
  if t.name in ('p','div','li','h1','h2','h3','h4','h5','h6','blockquote','pre','tr'):emit('\n')
  if not exit_node:stack.append((t,True));stack.extend((c,False) for c in reversed(list(t.children)))
 text=''.join(output);numeric=[p for p in pages if p['suffix'].isdecimal()]
 assert [int(p['suffix']) for p in numeric]==list(range(1,352))
 pmap={int(p['suffix']):p for p in numeric}
 assert all(pmap[n]['label']==f'[Pg {n}]' for n in range(252,258))
 spans=[[pmap[254]['text_offset'],pmap[257]['text_offset']],[pmap[252]['text_offset'],pmap[254]['text_offset']]]
 return {'extracted_text':text,'pages':pages,'window_spans':spans,'windows':[text[a:b] for a,b in spans]}
