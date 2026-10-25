"""Single-use offline census; retain all layouts, never fit or fetch."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile
from fl_decipher.yid_schema_v91 import role,scan,containment,summary

ROOT=Path(__file__).resolve().parents[1]
REG='experiments/yid_schema_v91.json'
OUT='runs/000091_yid_schema'
CODE=['experiments/yid_schema_v91.md','src/fl_decipher/yid_schema_v91.py',
      'scripts/yid_schema_v91.py','scripts/verify_yid_schema_v91.py','tests/test_yid_schema_v91.py']


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
    dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')


def prepare():
    paths=set(CODE+['reports/000090_deliverable_seal.json'])
    for p,h in read('reports/000090_deliverable_seal.json')['deliverable_hashes'].items():
        assert sha(p)==h,p
        paths.add(p)
    write(REG,{'experiment_id':'yid_schema_v91','registered_at_utc':now(),
               'input_hashes':{p:sha(p) for p in sorted(paths)},'expected_archive_entries':180,
               'candidate_number_range':[1,86],'network_requests':0,'new_predictions':False,
               'purpose':'exposed_annotation_schema_and_declared_provenance_census'})
    print('Frozen schema census; no document contents inspected.')


def run():
    reg=read(REG)
    for p,h in reg['input_hashes'].items():assert sha(p)==h,p
    (ROOT/OUT).mkdir(exist_ok=False)
    m={'experiment_id':'yid_schema_v91','state':'running','started_at_utc':now(),
       'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
    write(OUT+'/manifest.json',m)
    try:
        old=read('data/v90/inventory.json');archive_path=read('data/v90/acquisition.json')['hops'][-1]['body_path']
        assert old['integrity_pass'] and old['metadata_pass']
        members=[];raws={}
        with zipfile.ZipFile(ROOT/archive_path) as z:
            infos=z.infolist();assert len(infos)==len(old['entries'])==180
            for info,prior in zip(infos,old['entries']):
                r=role(info.orig_filename,info.is_dir())
                entry={'index':prior['index'],'name':info.orig_filename,'role':r,'bytes':prior['bytes']}
                assert info.orig_filename==prior['name']
                if r=='directory':entry['status']='directory'
                elif r=='packaging':
                    entry.update(status='opaque_packaging',sha256=prior['sha256'])
                else:
                    raw=z.read(info);assert len(raw)==prior['bytes'] and hashlib.sha256(raw).hexdigest()==prior['sha256']
                    entry['sha256']=prior['sha256'];raws[entry['index']]=raw
                    try:text=raw.decode('utf-8')
                    except UnicodeDecodeError as error:
                        entry.update(status='decode_failed',decode_error={'start':error.start,'end':error.end,'reason':error.reason})
                    else:entry.update(status='decoded',scan=scan(text,r=='article_candidate'))
                members.append(entry)
        combined=[e for e in members if e['role']=='combined']
        relations=[]
        for c in combined:
            for a in members:
                if a['role']=='article_candidate' and a['index'] in raws:
                    relations.append({'article_member_index':a['index'],'combined_member_index':c['index'],
                                      **containment(raws[a['index']],raws[c['index']])})
        numbers=Counter(int(e['name'].rsplit('/',1)[-1][:2]) for e in members if e['role']=='article_candidate')
        number_census={'counts':{str(k):v for k,v in sorted(numbers.items())},
                       'missing':[i for i in range(1,87) if not numbers[i]],
                       'repeated':[i for i in range(1,87) if numbers[i]>1]}
        write(OUT+'/member_ledger.json',members);write(OUT+'/combined_relations.json',relations)
        report={'experiment_id':'yid_schema_v91','summary':summary(members,relations),
                'candidate_filename_numbers':number_census,'archive_path':archive_path,
                'archive_sha256':sha(archive_path),'network_requests':0,'new_predictions':False,
                'native_text_corroborated':False,'verified_post_count':None,'corpus_admitted':False,
                'independent_group_capacity':None,'new_confirmation_units':0,'semantic_benchmark_qualifying_works':0}
        write(OUT+'/report.json',report)
        m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT)))
                 for p in sorted((ROOT/OUT).glob('*.json')) if p.name!='manifest.json'})
        print(json.dumps(report['summary'],indent=2))
        print(json.dumps({'missing_filename_numbers':number_census['missing'],'repeated_filename_numbers':number_census['repeated']},indent=2))
    except Exception as error:
        m.update(state='failed',finished_at_utc=now(),error=repr(error));raise
    finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run'])
    {'prepare':prepare,'run':run}[p.parse_args().action]()
