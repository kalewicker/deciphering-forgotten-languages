"""Offline independent packet/member/binding/blank-return audit."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import ast
import hashlib
import json
import zipfile
from verify_correspondence_v6 import check_hashes

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads((ROOT/path).read_text())


def main():
    cfg=read('experiments/kamri_review_handoff_v25.json');pre=read('data/v25/preflight.json')
    out=ROOT/'runs/000025_kamri_review_handoff';m=check_hashes(out);report=read('runs/000025_kamri_review_handoff/report.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < m['started_at_utc'] < m['finished_at_utc']
    for p,h in cfg['input_hashes'].items():
        assert sha((ROOT/p).read_bytes()) == h,p
    assert m['code_hashes'] == pre['code_hashes']
    assert [n['id'] for n in cfg['nominees']] == ['western_esoterism','risk_math']
    assert len(report['records']) == report['packets_prepared'] == report['packet_denominator'] == 2
    tree=ast.parse((ROOT/'src/fl_decipher/review_handoff_v25.py').read_text())
    instruction_text=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INSTRUCTIONS' for t in n.targets))
    for n,row in zip(cfg['nominees'],report['records'],strict=True):
        assert row['nominee_id'] == n['id'] and row['review_state'] == 'awaiting_independent_return'
        folder=ROOT/row['packet'];expected=set(n['members'])|{'INSTRUCTIONS.md','material_manifest.json','review_return_template.json'}
        assert {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()} == expected
        for name,path in n['members'].items():
            assert not (ROOT/path).is_symlink() and not (folder/name).is_symlink()
            assert (folder/name).read_bytes() == (ROOT/path).read_bytes(),name
        assert (folder/'INSTRUCTIONS.md').read_text() == instruction_text
        raw=(folder/'material_manifest.json').read_bytes();material=json.loads(raw)
        assert row['manifest_sha256'] == sha(raw)
        assert set(material['members']) == set(n['members'])|{'INSTRUCTIONS.md'}
        for name,data in material['members'].items():
            b=(folder/name).read_bytes();assert sha(b) == data['sha256'] and len(b) == data['bytes']
        for key,value in [('schema_version',1),('nominee_id',n['id']),('fl_url',n['fl_url']),('publisher_url',n['publisher_url']),
                          ('archive_timestamp',n['archive_timestamp']),('publisher_pages_one_based',n['pages_one_based']),
                          ('fl_material','dated_archive'),('candidate_source_pairing_disclosed',True),('prior_predictions_included',False),
                          ('source_relationship_accepted',False),('whole_post_source_coverage_established',False),('previously_exposed_development_group',True)]:
            assert material[key] == value,key
        for name in ['fl_post.txt','publisher_window.txt']:
            assert material['text_code_point_lengths'][name] == len((folder/name).read_text())
        form=json.loads((folder/'review_return_template.json').read_text())
        expected_form={'schema_version':1,'nominee_id':n['id'],'packet_manifest_sha256':sha(raw),
            'reviewer':{'name':None,'kind':None,'identifier':None,'independent_of_prior_predictions':None,'prior_exposure':None},
            'review_completed':False,'completed_at_utc':None,'language_observations':[],
            'source_relationship':'uncertain','coverage':'uncertain','statement_boundaries_checked':None,
            'evidence_pairs':[],'counterexamples':[],'uncertainty_notes':[]}
        assert form == expected_form
        invalid=row['blank_template_validation']
        assert invalid['structurally_valid'] is invalid['ready_for_adjudication'] is False and len(invalid['errors']) >= 8
        assert invalid['independence_externally_verified'] is invalid['source_identity_admitted'] is False
        assert invalid['semantic_labels_admitted'] == invalid['untouched_test_units_admitted'] == 0
        archive=ROOT/row['zip'];assert sha(archive.read_bytes()) == row['zip_sha256']
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist()) == expected and len(z.namelist()) == len(expected) == row['members']
            for info in z.infolist():
                p=PurePosixPath(info.filename)
                assert not p.is_absolute() and '..' not in p.parts
                assert info.date_time == (1980,1,1,0,0,0) and info.external_attr >> 16 == 0o100644
                assert z.read(info.filename) == (folder/info.filename).read_bytes()
    for key in ['independent_reviews_returned','independent_reviews_completed','source_identity_admissions',
                'semantic_labels_admitted','untouched_test_units_admitted','external_messages_sent','new_network_requests']:
        assert report[key] == 0,key
    assert report['evaluation_metrics'] is None and report['model_executed'] is report['prior_predictions_included'] is False
    assert report['review_state'] == 'awaiting_independent_return' and report['review_route'] == 'external_reviewer'
    assert report['candidate_pairing_disclosed'] is True
    prior=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent == out:
            continue
        check_hashes(path.parent);prior.append(path.parent.name)
    assert len(prior) == 24
    for path in (ROOT/'reports').glob('*_deliverable_seal.json'):
        seal=json.loads(path.read_text())
        for p,h in seal.get('deliverable_hashes',{}).items():
            assert sha((ROOT/p).read_bytes()) == h,p
    receipt={'state':'verified','run_manifest_sha256':sha((out/'manifest.json').read_bytes()),
             'packets_verified':2,'exact_member_sets_verified':True,'prior_runs_preserved':prior,
             'independent_reviews_completed':0,'semantic_labels_admitted':0,'evaluation_metrics':None}
    target=ROOT/'reports/000025_verification.json'
    if target.exists():
        saved=json.loads(target.read_text());assert {k:v for k,v in saved.items() if k != 'verified_at_utc'} == receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
