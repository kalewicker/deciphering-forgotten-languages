"""Offline reconstruction of E90 custody, metadata and ZIP integrity; no model code."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
from urllib.parse import urlsplit, urljoin
import zipfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
DATA='data/v90'
OUT='runs/000090_yid_archive'


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def permitted(url):
    try:
        u=urlsplit(url);parts=(u.hostname or '').lower().split('.')
        return u.scheme=='https' and u.username is None and u.password is None and u.port in (None,443) and not u.fragment and len(parts)>=2 and parts[-2:] in (['dropbox','com'],['dropboxusercontent','com'])
    except ValueError:return False


def reconstructed_inventory(path):
    try:z=zipfile.ZipFile(path)
    except (OSError,zipfile.BadZipFile) as e:
        return {'zip_readable':False,'entries':[],'archive_reasons':['unreadable_zip'],
                'metadata_pass':False,'integrity_pass':False,'error':type(e).__name__,
                'duplicate_classes':[],'suffix_counts':{}}
    with z:
        entries=[];normalized=[]
        for i,x in enumerate(z.infolist()):
            name=x.orig_filename;directory=x.is_dir();clean=name[:-1] if directory else name
            pp=PurePosixPath(clean);reasons=[]
            if (not clean or clean in ('.','..') or pp.is_absolute() or str(pp)!=clean or '..' in pp.parts or
                '\\' in name or re.match('[A-Za-z]:',name) or any(ord(c)<32 or ord(c)==127 for c in name)):
                reasons.append('unsafe_name')
            typ=stat.S_IFMT(x.external_attr>>16)
            if typ not in (0,stat.S_IFREG,stat.S_IFDIR) or (typ==stat.S_IFDIR and not directory) or (typ==stat.S_IFREG and directory):reasons.append('unsafe_type')
            if x.flag_bits&1:reasons.append('encrypted')
            if x.compress_type not in (0,8):reasons.append('unsupported_compression')
            if x.file_size>33554432:reasons.append('member_size_limit')
            if x.file_size>0 and (x.compress_size==0 or x.file_size>1000*x.compress_size):reasons.append('ratio_limit')
            if directory and x.file_size:reasons.append('nonempty_directory')
            normalized.append(unicodedata.normalize('NFC',clean).casefold())
            entries.append(dict(index=i,name=name,bytes=x.file_size,compressed_bytes=x.compress_size,
                                crc32=x.CRC,compression=x.compress_type,flags=x.flag_bits,unix_type=typ,
                                directory=directory,header_offset=x.header_offset,metadata_reasons=reasons,read_status='not_read'))
        counts=Counter(normalized)
        file_names={n for n,e in zip(normalized,entries) if not e['directory']}
        for n,e in zip(normalized,entries):
            if counts[n]>1:e['metadata_reasons'].append('name_collision')
            parents={str(p) for p in PurePosixPath(n).parents if str(p)!='.'}
            if parents&file_names:e['metadata_reasons'].append('file_ancestor')
        reasons=[]
        if not entries:reasons.append('empty_archive')
        if len(entries)>1000:reasons.append('entry_limit')
        if sum(x['bytes'] for x in entries if not x['directory'])>268435456:reasons.append('total_size_limit')
        suffixes=Counter()
        for e in entries:
            if not e['directory']:
                leaf=e['name'].split('/')[-1]
                suffixes[leaf.split('.')[-1].lower() if '.' in leaf else '<none>']+=1
        result=dict(zip_readable=True,entries=entries,archive_reasons=reasons,
                    metadata_pass=not reasons and all(not e['metadata_reasons'] for e in entries),
                    integrity_pass=False,duplicate_classes=[],suffix_counts=dict(sorted(suffixes.items())))
        if not result['metadata_pass']:return result
        total=0
        for x,e in zip(z.infolist(),entries):
            if e['directory']:
                e['read_status']='directory';continue
            try:
                size=0;checksum=0;digest=hashlib.sha256()
                with z.open(x) as f:
                    while True:
                        b=f.read(32768)
                        if not b:break
                        size+=len(b);total+=len(b)
                        if size>33554432 or total>268435456:raise ValueError('actual_size_limit')
                        checksum=zlib.crc32(b,checksum);digest.update(b)
                if size!=e['bytes'] or checksum!=e['crc32']:raise ValueError('size_or_crc_mismatch')
                e.update(read_status='verified',actual_bytes=size,sha256=digest.hexdigest(),crc_verified=True)
            except Exception as error:
                e.update(read_status='failed',error=type(error).__name__);return result
        dup=defaultdict(list)
        for e in entries:
            if not e['directory']:dup[e['sha256'],e['actual_bytes']].append(e['index'])
        result['duplicate_classes']=[dict(sha256=h,bytes=s,member_indices=ids)
                                     for (h,s),ids in sorted(dup.items()) if len(ids)>1]
        result['integrity_pass']=True
        return result


def verify():
    reg_path='experiments/yid_archive_v90.json';reg=read(reg_path);m=read(OUT+'/manifest.json')
    assert m['state']=='complete'
    assert m['input_hashes']==reg['input_hashes']|{reg_path:sha(reg_path)}
    for p,h in m['input_hashes'].items():assert sha(p)==h,p
    for p,h in m['output_hashes'].items():assert sha(p)==h,p
    for p,h in read('reports/000089_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
    offer=read('data/v89/observations.json')['offer_url']
    assert offer.endswith('&dl=0') and offer.count('dl=')==1
    retrieval=offer[:-1]+'1'
    assert read(DATA+'/retrieval.json')=={'offered_url':offer,'retrieval_url':retrieval,'transformation':'single_terminal_dl_0_to_1'}
    assert hashlib.sha256(retrieval.encode()).hexdigest()==reg['retrieval_url_sha256']
    receipt=read(DATA+'/acquisition.json');hops=receipt['hops']
    assert 1<=len(hops)<=5
    total=0
    for i,h in enumerate(hops):
        dest=f'{DATA}/acquisition/hop_{i:02}'
        assert h==read(dest+'/receipt.json') and h['index']==i
        intent=read(dest+'/intent.json')
        assert intent['url']==h['url'] and intent['method']=='GET' and permitted(h['url'])
        assert intent['reserved_at_utc']<=h['started_at_utc']<=h['finished_at_utc']
        if i==0:assert h['url']==retrieval
        else:
            previous=hops[i-1];assert previous['status'] in (301,302,303,307,308)
            location=[v for k,v in previous['headers'] if k.casefold()=='location']
            assert len(location)==1 and h['url']==urljoin(previous['url'],location[0])
        if 'body_path' in h:
            b=(ROOT/h['body_path']).read_bytes()
            assert len(b)==h['body_bytes'] and sha(h['body_path'])==h['body_sha256']
        else:assert h['body_bytes']==0
        total+=h['body_bytes']
    assert receipt['http_requests_reserved']==len(hops) and receipt['redirects_followed']==len(hops)-1
    assert total==receipt['aggregate_body_bytes']
    last=hops[-1];hs=defaultdict(list)
    for k,v in last['headers']:hs[k.casefold()].append(v)
    try:length_ok=not hs['content-length'] or (len(hs['content-length'])==1 and int(hs['content-length'][0])==last['body_bytes'])
    except ValueError:length_ok=False
    passed=bool(receipt['complete'] and last['status']==200 and permitted(last['url']) and
                0<last['body_bytes']<=total<=67108864 and length_ok and
                (not hs['content-encoding'] or hs['content-encoding']==['identity']))
    assert passed==receipt['transport_pass']
    if passed:inv=reconstructed_inventory(ROOT/last['body_path'])
    else:inv={'skipped':'transport_gate_failed','entries':[],'metadata_pass':False,'integrity_pass':False,'duplicate_classes':[],'suffix_counts':{}}
    assert inv==read(DATA+'/inventory.json')
    e=inv['entries']
    report=dict(experiment_id='yid_archive_v90',http_requests=len(hops),redirects_followed=len(hops)-1,
                aggregate_body_bytes=total,transport_pass=passed,zip_readable=inv.get('zip_readable',False),
                metadata_pass=inv['metadata_pass'],integrity_pass=inv['integrity_pass'],member_count=len(e),
                regular_member_count=sum(not x['directory'] for x in e),directory_count=sum(x['directory'] for x in e),
                advertised_expanded_bytes=sum(x['bytes'] for x in e if not x['directory']),
                verified_regular_members=sum(x['read_status']=='verified' for x in e),
                exact_duplicate_classes=len(inv['duplicate_classes']),
                extra_duplicate_copies=sum(len(c['member_indices'])-1 for c in inv['duplicate_classes']),
                suffix_counts=inv['suffix_counts'],author_claimed_post_count=86,verified_post_count=None,
                corpus_admitted=False,independent_group_capacity=None,new_predictions=False,
                documents_extracted=0,new_confirmation_units=0,semantic_benchmark_qualifying_works=0)
    assert report==read(OUT+'/report.json')
    print(json.dumps({'verified':True,'http_requests':len(hops),'transport_pass':passed,
                      'members':len(e),'integrity_pass':inv['integrity_pass'],
                      'verified_regular_members':report['verified_regular_members'],
                      'network_on_replay':False,'scientific_claims_validated':False},indent=2))


if __name__=='__main__':verify()
