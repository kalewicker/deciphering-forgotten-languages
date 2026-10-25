"""Descriptive schema/locator census of exact saved Unicode; no semantic admission."""
from collections import Counter
import re
from urllib.parse import urlsplit

HOST='forgottenlanguages-full.forgottenlanguages.org'
MARKER=re.compile(r'(?m)^([0-9]+)\.[ \t]*\r?$',re.ASCII)
LABEL=re.compile(r'(?m)^(Yid|English):[ \t]*\r?$',re.ASCII)
FIELD=re.compile(r'(?m)^([A-Za-z][A-Za-z -]{0,39}):[ \t]*([^\r\n]*)',re.ASCII)
URL=re.compile(r'''https?://[^\s<>"']+''')
LOCATORS={'original post','original url','post url','fl url'}


def role(name,directory=False):
    if directory:return 'directory'
    if name.startswith('__MACOSX/'):return 'packaging'
    leaf=name.rsplit('/',1)[-1]
    known={'00-INDEX.txt':'index','SOURCES.txt':'sources','ALL-TRANSLATIONS.txt':'combined'}
    if leaf in known:return known[leaf]
    m=re.fullmatch(r'(\d{2})-.+\.txt',leaf)
    return 'article_candidate' if m and 1<=int(m[1])<=86 else 'other'


def native_locator(value):
    try:
        u=urlsplit(value)
        return bool(u.scheme in ('http','https') and u.hostname==HOST and u.netloc==HOST and
                    re.fullmatch(r'/[0-9]{4}/[0-9]{2}/[^/]+\.html',u.path) and
                    not u.query and not u.fragment)
    except ValueError:return False


def url_kind(value):
    if native_locator(value):return 'native_article_shaped'
    try:
        u=urlsplit(value)
        if u.scheme not in ('http','https') or not u.hostname or any(c in value for c in '\\'):
            return 'malformed'
        return 'other_native' if u.hostname==HOST else 'external'
    except ValueError:return 'malformed'


def trimmed(text,start,end,chars=None):
    piece=text[start:end]
    left=len(piece)-len(piece.lstrip(chars));right=len(piece.rstrip(chars))
    return [start+left,max(start+left,start+right)]


def scan(text,article=False):
    all_numbered=list(MARKER.finditer(text))
    numbered=all_numbered if article else []
    header_end=all_numbered[0].start() if all_numbered else len(text)
    first=next((m for m in re.finditer(r'[^\r\n]+',text) if m[0].strip()),None)
    title={'span':[first.start(),first.end()],'value':first[0]} if first else None
    fields=[]
    for m in FIELD.finditer(text,0,header_end):
        a,b=trimmed(text,*m.span(2),' \t')
        key=' '.join(m[1].lower().split())
        fields.append({'label':m[1],'key':key,'label_span':list(m.span(1)),
                       'value':text[a:b],'value_span':[a,b]})
    loc=[f for f in fields if f['key'] in LOCATORS]
    langs=[f for f in fields if f['key']=='language']
    urls=[{'value':m[0],'span':[m.start(),m.end()],'kind':url_kind(m[0])} for m in URL.finditer(text)]
    blocks=[]
    for i,m in enumerate(numbered):
        end=numbered[i+1].start() if i+1<len(numbered) else len(text)
        labels=[{'label':x[1],'span':[x.start(),x.end()]} for x in LABEL.finditer(text,m.end(),end)]
        y=[x for x in labels if x['label']=='Yid'];e=[x for x in labels if x['label']=='English']
        reasons=[];ys=None;es=None
        if len(y)!=1:reasons.append('yid_label_count')
        if len(e)!=1:reasons.append('english_label_count')
        if len(y)==len(e)==1:
            if y[0]['span'][0]>=e[0]['span'][0]:reasons.append('label_order')
            else:
                ys=trimmed(text,y[0]['span'][1],e[0]['span'][0])
                es=trimmed(text,e[0]['span'][1],end)
                if ys[0]==ys[1]:reasons.append('empty_yid_region')
                if es[0]==es[1]:reasons.append('empty_english_region')
        blocks.append({'ordinal':i,'number':int(m[1]),'span':[m.start(),end],
                       'marker_span':[m.start(),m.end()],'labels':labels,'yid_region':ys,
                       'english_region':es,'paired_candidate':not reasons,'reasons':reasons})
    return {'characters':len(text),'title_candidate':title,'header_span':[0,header_end],'header_fields':fields,
            'declared_locators':[dict(f,syntax_valid=native_locator(f['value'])) for f in loc],
            'declared_languages':[f['value'] for f in langs],
            'locator_missing':not loc,'locator_repeated':len(loc)>1,
            'locator_conflict':len({f['value'] for f in loc})>1,
            'language_missing':not langs,'language_repeated':len(langs)>1,
            'language_conflict':len({f['value'] for f in langs})>1,
            'urls':urls,'blocks':blocks,'marker_numbers_consecutive':
                [b['number'] for b in blocks]==list(range(1,len(blocks)+1)) if blocks else None}


def occurrences(needle,haystack):
    if not needle:return []
    result=[];i=0
    while (i:=haystack.find(needle,i))>=0:
        result.append([i,i+len(needle)]);i+=1
    return result


def containment(raw,combined):
    return {'offset_unit':'bytes_in_combined_member','full_member':occurrences(raw,combined),
            'boundary_newline_view':occurrences(raw.strip(b'\r\n'),combined),
            'boundary_bytes_removed':len(raw)-len(raw.strip(b'\r\n'))}


def summary(members,relations):
    decoded=[m for m in members if m['status']=='decoded']
    articles=[m for m in decoded if m['role']=='article_candidate']
    blocks=[b for m in articles for b in m['scan']['blocks']]
    loc=[f for m in articles for f in m['scan']['declared_locators']]
    languages=Counter(v for m in articles for v in m['scan']['declared_languages'])
    urlcounts=Counter(u['kind'] for m in decoded for u in m['scan']['urls'])
    return {'members':len(members),'roles':dict(sorted(Counter(m['role'] for m in members).items())),
            'statuses':dict(sorted(Counter(m['status'] for m in members).items())),
            'decoded_documents':len(decoded),'decoded_article_candidates':len(articles),
            'article_candidates_without_blocks':sum(not m['scan']['blocks'] for m in articles),
            'numbered_blocks':len(blocks),'paired_candidate_blocks':sum(b['paired_candidate'] for b in blocks),
            'unpaired_blocks':sum(not b['paired_candidate'] for b in blocks),
            'block_reason_counts':dict(sorted(Counter(r for b in blocks for r in b['reasons']).items())),
            'articles_nonconsecutive_markers':sum(m['scan']['marker_numbers_consecutive'] is False for m in articles),
            'article_locator_fields':len(loc),'syntactically_valid_article_locator_fields':sum(f['syntax_valid'] for f in loc),
            'distinct_declared_article_locators':len({f['value'] for f in loc}),
            'articles_missing_locator':sum(m['scan']['locator_missing'] for m in articles),
            'articles_repeated_locator':sum(m['scan']['locator_repeated'] for m in articles),
            'articles_conflicting_locator':sum(m['scan']['locator_conflict'] for m in articles),
            'articles_missing_language':sum(m['scan']['language_missing'] for m in articles),
            'articles_conflicting_language':sum(m['scan']['language_conflict'] for m in articles),
            'declared_article_language_values':dict(sorted(languages.items())),
            'url_occurrences_by_kind':dict(sorted(urlcounts.items())),
            'distinct_literal_urls_all_documents':len({u['value'] for m in decoded for u in m['scan']['urls']}),
            'combined_relationships':len(relations),
            'combined_full_member_once':sum(len(r['full_member'])==1 for r in relations),
            'combined_boundary_view_once':sum(len(r['boundary_newline_view'])==1 for r in relations),
            'combined_full_member_missing':sum(not r['full_member'] for r in relations)}
