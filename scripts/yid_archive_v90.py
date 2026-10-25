"""Freeze one anonymous Dropbox GET chain; quarantine and inventory, never extract."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, HTTPRedirectHandler, build_opener
from fl_decipher.yid_archive_v90 import download_url, allowed_url, transport, inventory, MAX_BODY

ROOT = Path(__file__).resolve().parents[1]
DATA = 'data/v90'
OUT = 'runs/000090_yid_archive'
REG = 'experiments/yid_archive_v90.json'
CODE = ['experiments/yid_archive_v90.md','src/fl_decipher/yid_archive_v90.py',
        'scripts/yid_archive_v90.py','scripts/verify_yid_archive_v90.py','tests/test_yid_archive_v90.py']


def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(p,x):
    dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')


def prepare():
    offered=read('data/v89/observations.json')['offer_url']
    write(DATA+'/retrieval.json',{'offered_url':offered,'retrieval_url':download_url(offered),
                                 'transformation':'single_terminal_dl_0_to_1'})
    paths=set(CODE+[DATA+'/retrieval.json',DATA+'/dropbox_download_documentation.json',
                    'reports/000089_deliverable_seal.json'])
    for p,h in read('reports/000089_deliverable_seal.json')['deliverable_hashes'].items():
        assert sha(p)==h,p
        paths.add(p)
    write(REG,{'experiment_id':'yid_archive_v90','registered_at_utc':now(),
               'input_hashes':{p:sha(p) for p in sorted(paths)},
               'retrieval_url_sha256':hashlib.sha256(download_url(offered).encode()).hexdigest(),
               'logical_chains':1,'maximum_http_requests':5,'maximum_redirects':4,'retries':0,
               'chain_wall_seconds':60,'inventory_wall_seconds':30,'max_body_bytes':MAX_BODY,
               'max_entries':1000,'max_expanded_bytes':256*1024*1024,'max_member_bytes':32*1024*1024,
               'max_member_ratio':1000,'extraction':False,'new_predictions':False})
    print('Frozen single archive intake; no archive request performed.')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def deadline(seconds):
    def expired(*_): raise TimeoutError('registered_wall_deadline')
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,seconds)


def acquire(url):
    opener=build_opener(NoRedirect())
    hops=[];total=0;complete=False;failure=None
    deadline(60)
    try:
        for i in range(5):
            assert allowed_url(url)
            dest=f'{DATA}/acquisition/hop_{i:02}'
            write(dest+'/intent.json',{'url':url,'reserved_at_utc':now(),'method':'GET',
                                      'headers':{'Accept-Encoding':'identity','User-Agent':'FL-Decipher/0.1 E90 bounded archive intake'}})
            hop={'index':i,'url':url,'status':None,'headers':[],'body_bytes':0,'started_at_utc':now()}
            hops.append(hop)
            body_path=ROOT/dest/'body.bin'
            try:
                req=Request(url,headers={'Accept-Encoding':'identity','User-Agent':'FL-Decipher/0.1 E90 bounded archive intake'})
                try:response=opener.open(req,timeout=10)
                except HTTPError as error:response=error
                with response,body_path.open('xb') as body:
                    hop['status']=response.code;hop['headers']=list(response.headers.items())
                    while True:
                        block=response.read(min(65536,MAX_BODY-total+1))
                        if not block:break
                        body.write(block);hop['body_bytes']+=len(block);total+=len(block)
                        if total>MAX_BODY:raise ValueError('aggregate_body_limit')
                if hop['status'] in (301,302,303,307,308):
                    locations=[v for k,v in hop['headers'] if k.lower()=='location']
                    if len(locations)!=1:raise ValueError('redirect_location_count')
                    next_url=urljoin(url,locations[0])
                    if not allowed_url(next_url):raise ValueError('redirect_url_rejected')
                    if i==4:raise ValueError('redirect_limit')
                    url=next_url
                else:
                    complete=True
                    break
            except Exception as error:
                hop['error']=repr(error)
                raise
            finally:
                hop['finished_at_utc']=now()
                if body_path.exists():
                    hop['body_path']=str(body_path.relative_to(ROOT));hop['body_sha256']=sha(hop['body_path'])
                write(dest+'/receipt.json',hop)
    except Exception as error:failure=repr(error)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    receipt={'hops':hops,'http_requests_reserved':len(hops),'redirects_followed':max(0,len(hops)-1),
             'aggregate_body_bytes':total,'complete':complete,'failure':failure,
             'transport_pass':transport(hops,complete,total),'finished_at_utc':now()}
    write(DATA+'/acquisition.json',receipt)
    return receipt


def run():
    reg=read(REG)
    for p,h in reg['input_hashes'].items():assert sha(p)==h,p
    (ROOT/OUT).mkdir(exist_ok=False)
    manifest={'experiment_id':'yid_archive_v90','state':'running','started_at_utc':now(),
              'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
    write(OUT+'/manifest.json',manifest)
    try:
        receipt=acquire(read(DATA+'/retrieval.json')['retrieval_url'])
        if receipt['transport_pass']:
            deadline(30)
            try:inv=inventory(ROOT/receipt['hops'][-1]['body_path'])
            finally:signal.setitimer(signal.ITIMER_REAL,0)
        else:inv={'skipped':'transport_gate_failed','entries':[],'metadata_pass':False,'integrity_pass':False,'duplicate_classes':[],'suffix_counts':{}}
        write(DATA+'/inventory.json',inv)
        entries=inv['entries']
        report={'experiment_id':'yid_archive_v90','http_requests':len(receipt['hops']),
                'redirects_followed':receipt['redirects_followed'],'aggregate_body_bytes':receipt['aggregate_body_bytes'],
                'transport_pass':receipt['transport_pass'],'zip_readable':inv.get('zip_readable',False),
                'metadata_pass':inv['metadata_pass'],'integrity_pass':inv['integrity_pass'],
                'member_count':len(entries),'regular_member_count':sum(not e['directory'] for e in entries),
                'directory_count':sum(e['directory'] for e in entries),
                'advertised_expanded_bytes':sum(e['bytes'] for e in entries if not e['directory']),
                'verified_regular_members':sum(e['read_status']=='verified' for e in entries),
                'exact_duplicate_classes':len(inv['duplicate_classes']),
                'extra_duplicate_copies':sum(len(c['member_indices'])-1 for c in inv['duplicate_classes']),
                'suffix_counts':inv['suffix_counts'],'author_claimed_post_count':86,'verified_post_count':None,
                'corpus_admitted':False,'independent_group_capacity':None,'new_predictions':False,
                'documents_extracted':0,'new_confirmation_units':0,'semantic_benchmark_qualifying_works':0}
        write(OUT+'/report.json',report)
        paths=[p for p in (ROOT/DATA).rglob('*') if p.is_file()]+[ROOT/OUT/'report.json']
        manifest.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in sorted(paths)})
        print(json.dumps(report,indent=2))
    except Exception as error:
        manifest.update(state='failed',finished_at_utc=now(),error=repr(error))
        raise
    finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run'])
    {'prepare':prepare,'run':run}[parser.parse_args().action]()
