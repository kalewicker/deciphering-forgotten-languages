"""Read-only span, partition, join and aggregate replay; no adapter imports."""
import hashlib,json,re,zipfile
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def native(u):
    try:
        p=urlsplit(u)
        return p.scheme in ('https','http') and p.netloc=='forgottenlanguages-full.forgottenlanguages.org' and bool(re.fullmatch(r'/[0-9]{4}/[0-9]{2}/[^/]+\.html',p.path)) and not p.query and not p.fragment
    except ValueError:return False

def physical(text):
    start=0;out=[]
    while start<len(text):
        stop=text.find('\n',start);stop=len(text) if stop<0 else stop+1
        end=stop-int(text[stop-1:stop]=='\n');end-=int(text[end-1:end]=='\r')
        out.append((start,stop,end,text[start:end]));start=stop
    return out

def field_replay(text,start,end):
    fs=[]
    for a,b,c,value in physical(text[start:end]):
        m=re.fullmatch(r'[ \t]*([A-Za-z][A-Za-z ]*):[ \t]*([^\r\n]*)',value)
        if m:
            fs.append({'key':m[1],'value':m[2],'value_span':[start+a+m.start(2),start+a+m.end(2)],'span':[start+a,start+a+len(value)]})
    return fs

def cat_check(text,cat,source):
    headers=[]
    for a,b,c,value in physical(text):
        m=re.fullmatch(r'([0-9]+)\. ([^\r\n]+)',value)
        if m:headers.append((a,b,c,int(m[1]),m[2],a+m.start(2)))
    assert cat['prefix_span']==[0,headers[0][0] if headers else len(text)]
    assert len(headers)==len(cat['rows'])
    for j,(h,row) in enumerate(zip(headers,cat['rows'])):
        a,b,c,num,title,title_start=h;end=headers[j+1][0] if j+1<len(headers) else len(text)
        assert row['span']==[a,end] and row['number']==num and row['title']==title and row['title_span']==[title_start,c]
        assert row['fields']==field_replay(text,b,end)
        bullets=[(b+x,b+y,b+z,v) for x,y,z,v in physical(text[b:end]) if v.startswith('- ')] if source else []
        assert len(bullets)==len(row['claims'])
        for k,(bullet,claim) in enumerate(zip(bullets,row['claims'])):
            x,y,z,v=bullet;stop=bullets[k+1][0] if k+1<len(bullets) else end
            assert claim['span']==[x,stop] and claim['citation_span']==[x+2,z]
            assert claim['fields']==field_replay(text,x,stop)
            urls=[{'value':m[0],'span':[x+m.start(),x+m.end()]} for m in re.finditer(r'''https?://[^\s<>"']+''',text[x:stop])]
            assert claim['url_literals']==urls
    assert cat['characters']==len(text)

def main():
    reg=read('experiments/yid_adapter_v92.json');manifest=read('runs/000092_yid_adapter/manifest.json')
    assert manifest['state']=='complete'
    for mapping in [reg['input_hashes'],manifest['input_hashes'],manifest['output_hashes']]:
        for p,h in mapping.items():assert sha(p)==h,p
    ledger=read('runs/000092_yid_adapter/ledger.json');prior=read('runs/000091_yid_schema/member_ledger.json')
    docs={}
    with zipfile.ZipFile(ROOT/'data/v90/acquisition/hop_01/body.bin') as z:
        assert len(z.infolist())==len(prior)==180
        for info,p in zip(z.infolist(),prior):
            assert info.orig_filename==p['name']
            if p['role'] in ('article_candidate','index','sources','combined'):
                raw=z.read(info);assert hashlib.sha256(raw).hexdigest()==p['sha256'];docs[p['name']]=raw.decode('utf-8')
    assert read('runs/000092_yid_adapter/archive_accounting.json')==[{k:p[k] for k in ['index','name','role','status']} for p in prior]
    for label,member in [('index','index_member'),('sources','source_member')]:cat_check(docs[ledger[member]],ledger[label],label=='sources')
    value=lambda r,key:[f['value'] for f in r['fields'] if f['key']==key]
    articles=ledger['articles'];assert len(articles)==86
    assert {a['member'] for a in articles}=={p['name'] for p in prior if p['role']=='article_candidate'}
    reasons=Counter();total=0;resolved=0;bad=0;locs=Counter()
    for a in articles:
        text=docs[a['member']];leaf=a['member'].split('/')[-1];assert a['number']==int(leaf[:2]) and a['characters']==len(text)
        groups=[]
        for start,stop,end,v in physical(text):
            kind='separator' if not v.strip(' \t') else 'block'
            line={'span':[start,stop],'content_span':[start,end],'value':v}
            if groups and groups[-1]['kind']==kind:groups[-1]['span'][1]=stop;groups[-1]['lines'].append(line)
            else:groups.append({'kind':kind,'span':[start,stop],'lines':[line]})
        count=0;unsupported=False
        for g in groups:
            if g['kind']=='block':
                pair=len(g['lines'])==2;count+=pair;bad+=not pair;unsupported|=not pair
                g.update(paired_candidate=pair,reasons=[] if pair else ['expected_two_nonblank_lines'],candidate_yid_span=g['lines'][0]['content_span'] if pair else None,candidate_english_span=g['lines'][1]['content_span'] if pair else None)
        assert groups==a['parts'];total+=count
        ir=[r for r in ledger['index']['rows'] if leaf in value(r,'File')];sr=[r for r in ledger['sources']['rows'] if leaf in value(r,'Translation file')]
        rr=[]
        for tag,rows,key,urlkey in [('index',ir,'File','Original'),('source',sr,'Translation file','Original post')]:
            if len(rows)!=1:rr.append(tag+'_row_count');continue
            r=rows[0];u=value(r,urlkey)
            if value(r,key)!=[leaf]:rr.append(tag+'_filename_field_count')
            if r['number']!=a['number']:rr.append(tag+'_number_mismatch')
            if len(u)!=1 or not native(u[0]):rr.append(tag+'_locator_invalid_or_repeated')
        if len(ir)==len(sr)==1:
            if value(ir[0],'Original')!=value(sr[0],'Original post'):rr.append('locator_conflict')
            if ir[0]['title']!=sr[0]['title']:rr.append('catalog_title_conflict')
        cc=value(ir[0],'Sentence pairs') if len(ir)==1 else []
        declared=int(cc[0]) if len(cc)==1 and re.fullmatch('[0-9]+',cc[0]) else None
        if declared is None:rr.append('missing_or_invalid_declared_count')
        elif declared!=count:rr.append('declared_count_mismatch')
        if unsupported:rr.append('unsupported_blocks')
        if not groups:rr.append('empty_document')
        if len(sr)==1 and not sr[0]['claims']:rr.append('no_source_claims')
        expected={'index_row_spans':[r['span'] for r in ir],'source_row_spans':[r['span'] for r in sr], 'candidate_locators':value(ir[0],'Original') if len(ir)==1 else [],'declared_pairs':declared,'parsed_pairs':count,'resolved_layout_and_join':not rr,'reasons':rr}
        assert a['join']==expected;reasons.update(rr);resolved+=not rr;locs.update(expected['candidate_locators'])
    leaves={a['member'].split('/')[-1] for a in articles}
    unmatched={label:[r['span'] for r in ledger[label]['rows'] if len(value(r,key))!=1 or value(r,key)[0] not in leaves] for label,key in [('index','File'),('sources','Translation file')]}
    assert unmatched==ledger['unresolved_catalog_rows']
    assert ledger['duplicate_locator_literals']=={u:c for u,c in locs.items() if c>1}
    mentioned=re.findall(r'(?m)^- ([A-Z0-9-]+\.txt) — ',docs[ledger['index_member']])
    expected_summary={'candidate_documents':86,'index_rows':len(ledger['index']['rows']),'source_rows':len(ledger['sources']['rows']), 'parsed_candidate_pairs':total,'resolved_documents':resolved,'unsupported_blocks':bad,'declared_count_mismatch_documents':reasons['declared_count_mismatch'],'reason_counts':dict(reasons),'unresolved_index_rows':len(unmatched['index']),'unresolved_source_rows':len(unmatched['sources']),'distinct_joined_locator_literals':len(locs),'repeated_locator_classes':sum(c>1 for c in locs.values()),'source_claim_records':sum(len(r['claims']) for r in ledger['sources']['rows']),'missing_index_named_auxiliary_files':sorted(set(mentioned)-{n.split('/')[-1] for n in docs})}
    assert ledger['summary']==expected_summary==read('runs/000092_yid_adapter/report.json')['summary']
    print(json.dumps({'verified':True,'documents':86,'candidate_pairs':total,'resolved_documents':resolved,'sealed_input_files':len(reg['input_hashes']),'note':'Computational replay only; no native or semantic authentication.'},indent=2))
if __name__=='__main__':main()
