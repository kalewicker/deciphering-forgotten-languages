"""Literal annotation adapter. Layout and joins confer no semantic truth."""
import re
from collections import Counter
from fl_decipher.yid_schema_v91 import native_locator

ROW = re.compile(r'(?m)^([0-9]+)\. ([^\r\n]+)\r?$')
URL = re.compile(r'''https?://[^\s<>"']+''')


def lines(text):
    """LF/CRLF only; retain exact spans including line endings separately."""
    out=[]; pos=0
    for raw in text.split('\n'):
        end=pos+len(raw)
        if pos==len(text): break
        content_end=end-1 if raw.endswith('\r') else end
        out.append({'span':[pos, min(end+1,len(text))],
                    'content_span':[pos,content_end], 'value':text[pos:content_end]})
        pos=end+1
    return out


def units(text):
    """Partition every code point into whitespace separators or content blocks."""
    parts=[]
    for line in lines(text):
        kind='separator' if not line['value'].strip(' \t') else 'block'
        if parts and parts[-1]['kind']==kind:
            parts[-1]['span'][1]=line['span'][1]
            parts[-1]['lines'].append(line)
        else: parts.append({'kind':kind,'span':line['span'][:],'lines':[line]})
    for part in parts:
        if part['kind']=='block':
            part['paired_candidate']=len(part['lines'])==2
            part['reasons']=[] if part['paired_candidate'] else ['expected_two_nonblank_lines']
            part['candidate_yid_span']=part['lines'][0]['content_span'] if part['paired_candidate'] else None
            part['candidate_english_span']=part['lines'][1]['content_span'] if part['paired_candidate'] else None
    return parts


def fields(text,start,end):
    found=[]
    for m in re.finditer(r'(?m)^[ \t]*([A-Za-z][A-Za-z ]*):[ \t]*([^\r\n]*)',text[start:end]):
        a,b=m.span(2); a+=start;b+=start
        found.append({'key':m[1],'value':text[a:b],'value_span':[a,b],
                      'span':[start+m.start(),start+m.end()]})
    return found


def values(row,key): return [x['value'] for x in row['fields'] if x['key']==key]


def catalog(text,source=False):
    markers=list(ROW.finditer(text));rows=[]
    for i,m in enumerate(markers):
        end=markers[i+1].start() if i+1<len(markers) else len(text)
        fs=fields(text,m.end(),end)
        bullets=list(re.finditer(r'(?m)^- ([^\r\n]*)',text[m.end():end])) if source else []
        claims=[]
        for j,b in enumerate(bullets):
            start=m.end()+b.start(); stop=m.end()+bullets[j+1].start() if j+1<len(bullets) else end
            claims.append({'span':[start,stop],'citation_span':[m.end()+b.start(1),m.end()+b.end(1)],
                           'fields':fields(text,start,stop),
                           'url_literals':[{'value':u[0],'span':[start+u.start(),start+u.end()]} for u in URL.finditer(text[start:stop])]})
        rows.append({'number':int(m[1]),'title':m[2],'title_span':list(m.span(2)),
                     'span':[m.start(),end], 'fields':fs,'claims':claims})
    return {'prefix_span':[0,markers[0].start() if markers else len(text)],'rows':rows,'characters':len(text)}


def join(leaf,number,parts,index,source):
    ir=[r for r in index['rows'] if leaf in values(r,'File')]
    sr=[r for r in source['rows'] if leaf in values(r,'Translation file')]
    reasons=[]
    for label,rs,key,locator in [('index',ir,'File','Original'),('source',sr,'Translation file','Original post')]:
        if len(rs)!=1: reasons.append(label+'_row_count');continue
        r=rs[0]
        if values(r,key)!=[leaf]:reasons.append(label+'_filename_field_count')
        if r['number']!=number:reasons.append(label+'_number_mismatch')
        loc=values(r,locator)
        if len(loc)!=1 or not native_locator(loc[0]):reasons.append(label+'_locator_invalid_or_repeated')
    if len(ir)==len(sr)==1:
        if values(ir[0],'Original')!=values(sr[0],'Original post'):reasons.append('locator_conflict')
        if ir[0]['title']!=sr[0]['title']:reasons.append('catalog_title_conflict')
    parsed=sum(p.get('paired_candidate',False) for p in parts)
    counts=values(ir[0],'Sentence pairs') if len(ir)==1 else []
    declared=int(counts[0]) if len(counts)==1 and re.fullmatch(r'[0-9]+',counts[0]) else None
    if declared is None:reasons.append('missing_or_invalid_declared_count')
    elif declared!=parsed:reasons.append('declared_count_mismatch')
    if any(p['kind']=='block' and not p['paired_candidate'] for p in parts):reasons.append('unsupported_blocks')
    if not parts: reasons.append('empty_document')
    if len(sr)==1 and not sr[0]['claims']:reasons.append('no_source_claims')
    return {'index_row_spans':[r['span'] for r in ir],'source_row_spans':[r['span'] for r in sr],
            'candidate_locators':values(ir[0],'Original') if len(ir)==1 else [],
            'declared_pairs':declared,'parsed_pairs':parsed,'resolved_layout_and_join':not reasons,'reasons':reasons}


def census(documents):
    """documents maps exact archive names to exact decoded strings."""
    find=lambda leaf: [(n,t) for n,t in documents.items() if n.rsplit('/',1)[-1]==leaf]
    ins=find('00-INDEX.txt');src=find('SOURCES.txt');assert len(ins)==len(src)==1
    index=catalog(ins[0][1]);source=catalog(src[0][1],True)
    articles=[]
    for name,text in sorted(documents.items()):
        leaf=name.rsplit('/',1)[-1];m=re.fullmatch(r'([0-9]{2})-.+\.txt',leaf)
        if not m or not 1<=int(m[1])<=86:continue
        parts=units(text)
        articles.append({'member':name,'number':int(m[1]),'characters':len(text),'parts':parts,
                         'join':join(leaf,int(m[1]),parts,index,source)})
    leaves={a['member'].rsplit('/',1)[-1] for a in articles}
    unresolved_rows={}
    for label,cat,key in [('index',index,'File'),('sources',source,'Translation file')]:
        unresolved_rows[label]=[r['span'] for r in cat['rows'] if len(values(r,key))!=1 or values(r,key)[0] not in leaves]
    locs=Counter(u for a in articles for u in a['join']['candidate_locators'])
    mentions=[m[1] for m in re.finditer(r'(?m)^- ([A-Z0-9-]+\.txt) — ',ins[0][1])]
    available={n.rsplit('/',1)[-1] for n in documents}
    summary={'candidate_documents':len(articles),'index_rows':len(index['rows']),'source_rows':len(source['rows']),
             'parsed_candidate_pairs':sum(a['join']['parsed_pairs'] for a in articles),
             'resolved_documents':sum(a['join']['resolved_layout_and_join'] for a in articles),
             'unsupported_blocks':sum(p['kind']=='block' and not p['paired_candidate'] for a in articles for p in a['parts']),
             'declared_count_mismatch_documents':sum('declared_count_mismatch' in a['join']['reasons'] for a in articles),
             'reason_counts':dict(Counter(r for a in articles for r in a['join']['reasons'])),
             'unresolved_index_rows':len(unresolved_rows['index']),'unresolved_source_rows':len(unresolved_rows['sources']),
             'distinct_joined_locator_literals':len(locs),'repeated_locator_classes':sum(c>1 for c in locs.values()),
             'source_claim_records':sum(len(r['claims']) for r in source['rows']),
             'missing_index_named_auxiliary_files':sorted(set(mentions)-available)}
    return {'index_member':ins[0][0],'source_member':src[0][0],'index':index,'sources':source,
            'articles':articles,'unresolved_catalog_rows':unresolved_rows,
            'duplicate_locator_literals':{u:c for u,c in locs.items() if c>1},'summary':summary}
