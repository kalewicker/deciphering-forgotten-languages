"""Freeze developed adapter, then execute one offline complete census."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.yid_adapter_v92 import census
ROOT=Path(__file__).resolve().parents[1]
OUT='runs/000092_yid_adapter'
REG='experiments/yid_adapter_v92.json'
DEV='experiments/yid_adapter_v92_development.json'
ARCHIVE='data/v90/acquisition/hop_01/body.bin'
CODE=['experiments/yid_adapter_v92.md','experiments/yid_adapter_v92_rules.md',
      'src/fl_decipher/yid_adapter_v92.py','scripts/yid_adapter_v92.py',
      'scripts/verify_yid_adapter_v92.py','tests/test_yid_adapter_v92.py',
      'src/fl_decipher/yid_schema_v91.py','data/v92/development_sample.json',DEV]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
    with (ROOT/p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def freeze():
    old=read(DEV)['input_hashes']
    for p,h in old.items():assert sha(p)==h,p
    write(REG,{'experiment_id':'yid_adapter_v92','frozen_at_utc':now(),
               'input_hashes':{p:sha(p) for p in sorted(set(old)|set(CODE))},
               'development_exposure':'five fixed member prefixes; see local sample receipt',
               'network_requests':0,'model_runs':0,'complete_census_attempts':1})
    print('Adapter frozen before full census.')
def run():
    reg=read(REG)
    for p,h in reg['input_hashes'].items():assert sha(p)==h,p
    (ROOT/OUT).mkdir(exist_ok=False)
    manifest={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
    write(OUT+'/manifest.json',manifest)
    try:
        prior=read('runs/000091_yid_schema/member_ledger.json');docs={};account=[]
        with zipfile.ZipFile(ROOT/ARCHIVE) as z:
            assert len(z.infolist())==len(prior)==180
            for info,entry in zip(z.infolist(),prior):
                assert info.orig_filename==entry['name']
                account.append({k:entry[k] for k in ['index','name','role','status']})
                if entry['role'] in ('index','sources','article_candidate','combined'):
                    raw=z.read(info);assert hashlib.sha256(raw).hexdigest()==entry['sha256']
                    docs[entry['name']]=raw.decode('utf-8')
        ledger=census(docs)
        assert len(ledger['articles'])==86
        write(OUT+'/ledger.json',ledger);write(OUT+'/archive_accounting.json',account)
        report={'experiment_id':'yid_adapter_v92','summary':ledger['summary'],'archive_entries':len(account),
                'network_requests':0,'model_runs':0,'native_text_corroborated':False,
                'semantic_labels_validated':False,'independent_group_capacity':None,
                'corpus_admitted':False,'semantic_benchmark_qualifying_works':0}
        write(OUT+'/report.json',report)
        manifest.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in sorted((ROOT/OUT).glob('*.json')) if p.name!='manifest.json'})
        print(json.dumps(report,indent=2))
    except Exception as e:
        manifest.update(state='failed',finished_at_utc=now(),error=repr(e));raise
    finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);{'freeze':freeze,'run':run}[p.parse_args().action]()
