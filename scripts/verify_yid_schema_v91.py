"""Offline line-oriented schema reconstruction; no production census imports."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT='runs/000091_yid_schema'
HOST='forgottenlanguages-full.forgottenlanguages.org'


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def member_role(name,isdir):
    if isdir:return 'directory'
    if name.split('/')[0]=='__MACOSX':return 'packaging'
    leaf=name.split('/')[-1]
    if leaf=='00-INDEX.txt':return 'index'
    if leaf=='SOURCES.txt':return 'sources'
    if leaf=='ALL-TRANSLATIONS.txt':return 'combined'
    number=leaf[:2]
    if len(leaf)>7 and number in [f'{n:02}' for n in range(1,87)] and leaf[2]=='-' and leaf.endswith('.txt'):
        return 'article_candidate'
    return 'other'


def valid(value):
    try:
        u=urlsplit(value);p=u.path.split('/')
        return bool(u.scheme in ('http','https') and u.hostname==HOST and u.netloc==HOST and
                    len(p)==4 and p[0]=='' and re.fullmatch('[0-9]{4}',p[1]) and
                    re.fullmatch('[0-9]{2}',p[2]) and len(p[3])>5 and p[3].endswith('.html') and
                    not u.query and not u.fragment)
    except ValueError:return False


def classification(value):
    if valid(value):return 'native_article_shaped'
    try:
        u=urlsplit(value)
        if u.scheme not in ('http','https') or not u.hostname or '\\' in value:return 'malformed'
        return 'other_native' if u.hostname==HOST else 'external'
    except ValueError:return 'malformed'


def bounds(s,a,b,horizontal=False):
    skip=lambda c:c in ' \t' if horizontal else c.isspace()
    while a<b and skip(s[a]):a+=1
    while b>a and skip(s[b-1]):b-=1
    return [a,b]


def document(text,article):
    lines=[];start=0
    for line in text.split('\n'):
        lines.append((start,line));start+=len(line)+1
    markers=[];all_labels=[]
    for a,line in lines:
        m=re.fullmatch(r'([0-9]+)\.[ \t]*\r?',line)
        if m:markers.append((a,a+len(line),int(m[1])))
        label=re.fullmatch(r'(Yid|English):[ \t]*\r?',line)
        if label:all_labels.append({'label':label[1],'span':[a,a+len(line)]})
    end=markers[0][0] if markers else len(text)
    fields=[]
    for a,line in lines:
        if a>=end:break
        f=re.match(r'([A-Za-z][A-Za-z -]{0,39}):[ \t]*([^\r\n]*)',line)
        if not f:continue
        span=bounds(text,a+f.start(2),a+f.end(2),True)
        fields.append(dict(label=f[1],key=' '.join(f[1].lower().split()),label_span=[a+f.start(1),a+f.end(1)],
                           value=text[slice(*span)],value_span=span))
    title=None;a=0
    for b in range(len(text)+1):
        if b==len(text) or text[b] in '\r\n':
            if a<b and text[a:b].strip():
                title=dict(span=[a,b],value=text[a:b]);break
            a=b+1
    loc=[f for f in fields if f['key'] in ('original post','original url','post url','fl url')]
    langs=[f for f in fields if f['key']=='language']
    urls=[];last_end=-1
    for m in re.finditer('https?://',text):
        if m.start()<last_end:continue
        a=m.start();b=m.end()
        while b<len(text) and not text[b].isspace() and text[b] not in '<>\"\'':b+=1
        value=text[a:b]
        urls.append(dict(value=value,span=[a,b],kind=classification(value)));last_end=b
    blocks=[]
    if article:
        for i,(a,b,number) in enumerate(markers):
            stop=markers[i+1][0] if i+1<len(markers) else len(text)
            labels=[x for x in all_labels if b<=x['span'][0]<stop]
            y=[x for x in labels if x['label']=='Yid'];e=[x for x in labels if x['label']=='English']
            reasons=[];ys=None;es=None
            if len(y)!=1:reasons.append('yid_label_count')
            if len(e)!=1:reasons.append('english_label_count')
            if len(y)==1 and len(e)==1:
                if y[0]['span'][0]>=e[0]['span'][0]:reasons.append('label_order')
                else:
                    ys=bounds(text,y[0]['span'][1],e[0]['span'][0]);es=bounds(text,e[0]['span'][1],stop)
                    if ys[0]==ys[1]:reasons.append('empty_yid_region')
                    if es[0]==es[1]:reasons.append('empty_english_region')
            blocks.append(dict(ordinal=i,number=number,span=[a,stop],marker_span=[a,b],labels=labels,
                               yid_region=ys,english_region=es,paired_candidate=not reasons,reasons=reasons))
    return dict(characters=len(text),title_candidate=title,header_span=[0,end],header_fields=fields,
                declared_locators=[dict(f,syntax_valid=valid(f['value'])) for f in loc],
                declared_languages=[f['value'] for f in langs],locator_missing=not loc,locator_repeated=len(loc)>1,
                locator_conflict=len(set(f['value'] for f in loc))>1,language_missing=not langs,
                language_repeated=len(langs)>1,language_conflict=len(set(f['value'] for f in langs))>1,
                urls=urls,blocks=blocks,marker_numbers_consecutive=
                [b['number'] for b in blocks]==list(range(1,len(blocks)+1)) if blocks else None)


def byte_hits(needle,haystack):
    if not needle:return []
    return [[m.start(),m.start()+len(needle)] for m in re.finditer(b'(?='+re.escape(needle)+b')',haystack)]


def summarize(members,relations):
    dec=[m for m in members if m['status']=='decoded'];art=[m for m in dec if m['role']=='article_candidate']
    blocks=[b for m in art for b in m['scan']['blocks']];loc=[f for m in art for f in m['scan']['declared_locators']]
    scans=[m['scan'] for m in art]
    return dict(members=len(members),roles=dict(sorted(Counter(m['role'] for m in members).items())),
                statuses=dict(sorted(Counter(m['status'] for m in members).items())),decoded_documents=len(dec),
                decoded_article_candidates=len(art),article_candidates_without_blocks=sum(not s['blocks'] for s in scans),
                numbered_blocks=len(blocks),paired_candidate_blocks=sum(b['paired_candidate'] for b in blocks),
                unpaired_blocks=sum(not b['paired_candidate'] for b in blocks),
                block_reason_counts=dict(sorted(Counter(x for b in blocks for x in b['reasons']).items())),
                articles_nonconsecutive_markers=sum(s['marker_numbers_consecutive'] is False for s in scans),
                article_locator_fields=len(loc),syntactically_valid_article_locator_fields=sum(f['syntax_valid'] for f in loc),
                distinct_declared_article_locators=len(set(f['value'] for f in loc)),
                articles_missing_locator=sum(s['locator_missing'] for s in scans),
                articles_repeated_locator=sum(s['locator_repeated'] for s in scans),
                articles_conflicting_locator=sum(s['locator_conflict'] for s in scans),
                articles_missing_language=sum(s['language_missing'] for s in scans),
                articles_conflicting_language=sum(s['language_conflict'] for s in scans),
                declared_article_language_values=dict(sorted(Counter(v for s in scans for v in s['declared_languages']).items())),
                url_occurrences_by_kind=dict(sorted(Counter(u['kind'] for m in dec for u in m['scan']['urls']).items())),
                distinct_literal_urls_all_documents=len(set(u['value'] for m in dec for u in m['scan']['urls'])),
                combined_relationships=len(relations),combined_full_member_once=sum(len(r['full_member'])==1 for r in relations),
                combined_boundary_view_once=sum(len(r['boundary_newline_view'])==1 for r in relations),
                combined_full_member_missing=sum(not r['full_member'] for r in relations))


def verify():
    rp='experiments/yid_schema_v91.json';reg=read(rp);manifest=read(OUT+'/manifest.json')
    assert manifest['state']=='complete' and manifest['input_hashes']==reg['input_hashes']|{rp:sha(rp)}
    for p,h in manifest['input_hashes'].items():assert sha(p)==h,p
    for p,h in manifest['output_hashes'].items():assert sha(p)==h,p
    for p,h in read('reports/000090_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
    archive=read('data/v90/acquisition.json')['hops'][-1]['body_path'];prior=read('data/v90/inventory.json')['entries']
    expected=[];raws={}
    with zipfile.ZipFile(ROOT/archive) as z:
        assert len(z.infolist())==len(prior)==180
        for x,p in zip(z.infolist(),prior):
            assert x.orig_filename==p['name']
            r=member_role(x.orig_filename,x.is_dir());entry=dict(index=p['index'],name=x.orig_filename,role=r,bytes=p['bytes'])
            if r=='directory':entry['status']='directory'
            else:
                raw=z.read(x);assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256']
                entry['sha256']=p['sha256']
                if r=='packaging':entry['status']='opaque_packaging'
                else:
                    raws[p['index']]=raw
                    try:text=raw.decode('utf-8')
                    except UnicodeDecodeError as e:entry.update(status='decode_failed',decode_error=dict(start=e.start,end=e.end,reason=e.reason))
                    else:entry.update(status='decoded',scan=document(text,r=='article_candidate'))
            expected.append(entry)
    actual=read(OUT+'/member_ledger.json');assert len(actual)==180
    for a,b in zip(actual,expected):assert a==b,('member_disagreement',a['index'])
    relations=[]
    for c in expected:
        if c['role']!='combined':continue
        for a in expected:
            if a['role']!='article_candidate' or a['index'] not in raws:continue
            raw=raws[a['index']];start=0;end=len(raw)
            while start<end and raw[start] in (10,13):start+=1
            while end>start and raw[end-1] in (10,13):end-=1
            relations.append(dict(article_member_index=a['index'],combined_member_index=c['index'],
                                  offset_unit='bytes_in_combined_member',full_member=byte_hits(raw,raws[c['index']]),
                                  boundary_newline_view=byte_hits(raw[start:end],raws[c['index']]),boundary_bytes_removed=len(raw)-(end-start)))
    assert relations==read(OUT+'/combined_relations.json')
    numbers=Counter(int(m['name'].split('/')[-1][:2]) for m in expected if m['role']=='article_candidate')
    report=dict(experiment_id='yid_schema_v91',summary=summarize(expected,relations),
                candidate_filename_numbers=dict(counts={str(k):v for k,v in sorted(numbers.items())},
                                                missing=[i for i in range(1,87) if not numbers[i]],
                                                repeated=[i for i in range(1,87) if numbers[i]>1]),
                archive_path=archive,archive_sha256=sha(archive),network_requests=0,new_predictions=False,
                native_text_corroborated=False,verified_post_count=None,corpus_admitted=False,
                independent_group_capacity=None,new_confirmation_units=0,semantic_benchmark_qualifying_works=0)
    assert report==read(OUT+'/report.json')
    print(json.dumps(dict(verified=True,members=180,decoded_documents=report['summary']['decoded_documents'],
                          numbered_blocks=report['summary']['numbered_blocks'],
                          paired_candidate_blocks=report['summary']['paired_candidate_blocks'],
                          network_requests=0,new_predictions=False,scientific_claims_validated=False),indent=2))


if __name__=='__main__':verify()
