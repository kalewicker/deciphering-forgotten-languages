"""Separate train, learn/freeze and test-generation stages."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
from fl_decipher.synthetic_transfer_v32 import training,learn,prepare_tests

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')


def main():
    cfg=read('experiments/synthetic_transfer_v32.json');pre=read('data/v32/preflight.json')
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert sha(p)==h,p
    folder=ROOT/'data/v32';stage=sys.argv[1]
    if stage=='train':
        assert not (folder/'training.json').exists() and not (folder/'training_receipt.json').exists()
        data=training(cfg);write(folder/'training.json',data)
        receipt={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'training_sha256':sha('data/v32/training.json'),'units':len(data['units']),'tests_generated':0}
        write(folder/'training_receipt.json',receipt);print(json.dumps(receipt))
    elif stage=='learn':
        assert not (folder/'frozen_mapping.json').exists() and not (folder/'public_cases.json').exists()
        receipt=read('data/v32/training_receipt.json');assert sha('data/v32/training.json')==receipt['training_sha256']
        model=learn(read('data/v32/training.json'),cfg['minimum_training_units'])
        frozen={'learned_at_utc':datetime.now(timezone.utc).isoformat(),'training_sha256':receipt['training_sha256'],
                'training_receipt_sha256':sha('data/v32/training_receipt.json'),'model':model}
        write(folder/'frozen_mapping.json',frozen)
        print(json.dumps({'entries':len(model['entries']),'statuses':{s:sum(r['status']==s for r in model['ledger'].values()) for s in ['admitted','conflict','insufficient_support']},'tests_generated':0}))
    elif stage=='tests':
        targets=[folder/n for n in ['public_cases.json','oracle.json','availability.json','test_preparation_receipt.json']]
        assert not any(p.exists() for p in targets)
        frozen=read('data/v32/frozen_mapping.json');assert frozen['training_sha256']==sha('data/v32/training.json')
        public,oracle,availability=prepare_tests(cfg,frozen['model'])
        assert (len(oracle['bases']),len(oracle['queries']),len(public['cases']))==(84,420,2100)
        for p,v in zip(targets[:3],[public,oracle,availability],strict=True):write(p,v)
        receipt={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'mapping_sha256':sha('data/v32/frozen_mapping.json'),'parents':84,'queries':420,'panels':2100,
                 'pair_alignments_computed':0,'output_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in targets[:3]}}
        write(targets[-1],receipt)
        print(json.dumps({'counts':receipt|{'output_hashes':'sealed'},'potentially_available_queries':sum(a['potentially_available'] for a in availability['availability'].values())},indent=2))
    else:raise ValueError(stage)


if __name__=='__main__':main()
