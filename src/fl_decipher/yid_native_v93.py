"""Frozen single-page correspondence, not semantic validation."""
import re
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Doctype
BLOCKS={'p','div','li','h1','h2','h3','h4','h5','h6','blockquote','pre'}
OMIT={'script','style','noscript','template'}
def normalize(s):return re.sub(r'\s+',' ',s).strip()
def occurrences(needle,text):
    assert needle
    spans=[];start=0
    while (start:=text.find(needle,start))>=0:
        spans.append([start,start+len(needle)]);start+=1
    return spans

def extract(body):
    chunks=[];offset=0
    def emit(s,kind):
        nonlocal offset
        if s:chunks.append({'span':[offset,offset+len(s)],'text':s,'kind':kind});offset+=len(s)
    def visit(node):
        if isinstance(node,(Comment,Doctype)):return
        if isinstance(node,NavigableString):emit(str(node),'text');return
        if not isinstance(node,Tag) or node.name in OMIT:return
        if node.name=='br':emit('\n','br');return
        if node.name in BLOCKS:emit('\n','block_start')
        for child in node.children:visit(child)
        if node.name in BLOCKS:emit('\n','block_end')
    visit(body)
    return ''.join(c['text'] for c in chunks),chunks

def compare(text,targets):
    rows=[];cursor=0
    for t in targets:
        spans=occurrences(t,text);chosen=next((p for p in spans if p[0]>=cursor),None)
        if chosen:cursor=chosen[1]
        rows.append({'occurrences':spans,'count':len(spans),'ordered_span':chosen})
    return {'rows':rows,'denominator':len(targets),'matched':sum(bool(r['count']) for r in rows),'ordered_matched':sum(r['ordered_span'] is not None for r in rows)}

def assess(raw,target,reported_requested,reported_final,targets):
    if len(raw)>16*1024*1024:return {'admissible':False,'reasons':['oversized_html'],'comparison':None}
    try:html=raw.decode('utf-8')
    except UnicodeDecodeError:return {'admissible':False,'reasons':['utf8_decode_failed'],'comparison':None}
    soup=BeautifulSoup(html,'html.parser')
    saved=re.findall(r'<!--\s*saved from url=\(\d+\)([^\s<>]+)\s*-->',html)
    identities=saved+[x.get('href','') for x in soup.select('link[rel~=canonical]')]+[x.get('content','') for x in soup.select('meta[property="og:url"]')]
    bodies=soup.select('.post-body');reasons=[]
    if target not in identities:reasons.append('no_positive_origin_binding')
    if any(u!=target for u in identities):reasons.append('conflicting_identity')
    if reported_requested!=target:reasons.append('requested_url_unconfirmed_or_wrong')
    if reported_final!=target:reasons.append('final_url_unconfirmed_or_wrong')
    if len(bodies)!=1:reasons.append('post_body_count')
    result={'admissible':not reasons,'reasons':reasons,'identity_values':identities,'post_body_count':len(bodies),'comparison':None}
    if reasons:return result
    text,chunks=extract(bodies[0]);norm=normalize(text)
    result.update(extracted_text=text,extraction_chunks=chunks,normalized_text=norm,
                  comparison={'literal':compare(text,targets),'whitespace':compare(norm,[normalize(t) for t in targets])})
    return result
