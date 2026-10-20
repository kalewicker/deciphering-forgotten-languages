"""Complete structural target scope and literal token sequence presence only."""
from collections import defaultdict
import hashlib
import re
import unicodedata
from bs4 import BeautifulSoup,Tag

MARKER='flv68absencecontrol20261020'
WIDTH=12

def norm(token):return unicodedata.normalize('NFC',token).casefold()
def tokens(text):return [{'literal':m.group(),'normalized':norm(m.group()),'span':list(m.span())} for m in re.finditer(r'\S+',text)]

def target_scope(raw,export,inventory,width=WIDTH):
    soup=BeautifulSoup(raw,'html.parser');dom=soup.select('*');bodies=soup.select('div.post-body')
    if len(bodies)!=1:raise ValueError('unique body required')
    body=bodies[0];children=list(body.children)
    if len(inventory['boundary_match_run_ids'])!=1:raise ValueError('unique frozen reference boundary required')
    boundary=inventory['boundary_match_run_ids'][0]
    if not inventory['runs'][boundary]['text'].startswith('Aissen, Judith (2003).'):raise ValueError('boundary mismatch')
    for t in body.find_all(['script','style','noscript']):t.decompose()
    if body.get_text(' ',strip=True)!=export['text'] or hashlib.sha256(raw).hexdigest()!=export['parent_sha256']:
        raise ValueError('raw/export mismatch')
    ledger=[];blocks=[];queries=[]
    for run in inventory['runs']:
        owner=children[run['direct_child_index']]
        value=owner.get_text(' ',strip=True) if isinstance(owner,Tag) else str(owner).strip()
        if value!=run['text'] or export['text'][slice(*run['span'])]!=value:raise ValueError('owner span mismatch')
        if isinstance(owner,Tag) and dom[run['owner_dom_tag_index']] is not owner:raise ValueError('DOM locator mismatch')
        included=run['run_id']<boundary and isinstance(owner,Tag) and owner.name=='div' and owner.get('align','').casefold()=='justify'
        reason='included_structural_prose_block' if included else 'at_or_after_reference_boundary' if run['run_id']>=boundary else 'pre_reference_non_prose_owner'
        ledger.append({'run_id':run['run_id'],'owner_dom_tag_index':run['owner_dom_tag_index'],'body_span':run['span'],'included':included,'reason':reason,'block_id':len(blocks) if included else None})
        if not included:continue
        ts=tokens(value);bid=len(blocks)
        blocks.append({'block_id':bid,'run_id':run['run_id'],'body_span':run['span'],'text':value,'token_count':len(ts),'secondary_query_count':max(0,len(ts)-width+1)})
        for kind,a,b in [('whole_block',0,len(ts))]+[('window12',i,i+width) for i in range(max(0,len(ts)-width+1))]:
            start=run['span'][0]+ts[a]['span'][0];end=run['span'][0]+ts[b-1]['span'][1]
            queries.append({'query_id':len(queries),'block_id':bid,'run_id':run['run_id'],'kind':kind,'block_token_span':[a,b],
                'body_span':[start,end],'text':export['text'][start:end],'normalized_tokens':[t['normalized'] for t in ts[a:b]]})
    return {'raw_parent_sha256':export['parent_sha256'],'body_text_sha256':export['text_sha256'],'boundary_run_id':boundary,'width':width,'ledger':ledger,'blocks':blocks,'queries':queries}


def source_scope(pages):
    rows=[];all_tokens=[];parts=[];at=0
    for page in pages:
        text=page['text'];start=at+bool(parts)
        rows.append({'page':page['page'],'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'unicode_characters':len(text),
            'document_span':[start,start+len(text)],'token_span':[len(all_tokens),len(all_tokens)+len(tokens(text))]})
        for t in tokens(text):all_tokens.append({'page':page['page'],'page_span':t['span'],'document_span':[start+t['span'][0],start+t['span'][1]],'literal':t['literal'],'normalized':t['normalized']})
        parts.append(text);at=start+len(text)
    document='\n'.join(parts)
    return {'pages':rows,'document_characters':len(document),'document_sha256':hashlib.sha256(document.encode()).hexdigest(),'tokens':all_tokens,'separator':'single newline between unchanged page strings'}


class Matcher:
    def __init__(self,source,width=WIDTH):
        self.source=source;self.width=width;self.values=[t['normalized'] for t in source['tokens']];self.index=defaultdict(list)
        for i in range(max(0,len(self.values)-width+1)):self.index[tuple(self.values[i:i+width])].append(i)
    def hits(self,query):
        if not query:raise ValueError('empty queries are not matchable')
        n=len(query);candidates=self.index.get(tuple(query[:self.width]),[]) if n>=self.width else range(max(0,len(self.values)-n+1))
        found=[]
        for i in candidates:
            if self.values[i:i+n]!=query:continue
            matched=self.source['tokens'][i:i+n];page_spans=[]
            for token in matched:
                if not page_spans or page_spans[-1]['page']!=token['page']:
                    page_spans.append({'page':token['page'],'span':list(token['page_span'])})
                else:page_spans[-1]['span'][1]=token['page_span'][1]
            for row in page_spans:row['quote']=self.source['pages'][row['page']-1]['text'][slice(*row['span'])]
            found.append({'source_token_span':[i,i+n],'document_span':[matched[0]['document_span'][0],matched[-1]['document_span'][1]],'page_spans':page_spans})
        return found


def assess(target,source,marker=MARKER):
    matcher=Matcher(source);values=[t['normalized'] for t in source['tokens']]
    collision=any(marker in t['normalized'] for t in source['tokens']) or any(marker in norm(b['text']) for b in target['blocks'])
    results=[]
    for query in target['queries']:
        hits=matcher.hits(query['normalized_tokens']);results.append({'query_id':query['query_id'],'block_id':query['block_id'],'kind':query['kind'],'hits':hits,'present':bool(hits)})
    positives=[];negatives=[]
    for page in source['pages']:
        a,b=page['token_span'];prefix=values[a:min(b,a+WIDTH)];hits=matcher.hits(prefix) if prefix else []
        positives.append({'page':page['page'],'normalized_tokens':prefix,'hits':hits,'passed':bool(prefix and any(h['source_token_span']==[a,a+len(prefix)] for h in hits))})
        negative=prefix+[marker];nh=matcher.hits(negative)
        negatives.append({'page':page['page'],'normalized_tokens':negative,'hits':nh,'passed':not collision and not nh})
    counts=[]
    for block in target['blocks']:
        rows=[r for r in results if r['block_id']==block['block_id']]
        counts.append({'block_id':block['block_id'],'run_id':block['run_id'],'token_count':block['token_count'],
            'whole_block_present':any(r['present'] for r in rows if r['kind']=='whole_block'),
            'secondary_query_count':sum(r['kind']=='window12' for r in rows),'secondary_queries_present':sum(r['present'] for r in rows if r['kind']=='window12')})
    return {'results':results,'positive_controls':positives,'negative_controls':negatives,'marker_collision':collision,
        'controls_passed':bool(source['pages'] and all(r['passed'] for r in positives+negatives)),'per_block':counts,
        'source_hit_pages':sorted({p['page'] for r in results for h in r['hits'] for p in h['page_spans']})}
