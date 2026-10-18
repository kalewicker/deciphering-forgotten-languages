"""Generate the sealed public corpus, separate oracle and pre-score availability."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from fl_decipher.synthetic_mechanisms_v31 import prepare

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())


def main():
    cfg=read('experiments/synthetic_mechanisms_v31.json');pre=read('data/v31/preflight.json')
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for name,h in hashes.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    targets=[ROOT/'data/v31'/name for name in ['public_cases.json','oracle.json','availability.json','preparation_receipt.json']]
    assert not any(p.exists() for p in targets)
    public,oracle,availability=prepare(cfg)
    assert len(oracle['bases'])==40 and len(oracle['queries'])==200 and len(public['cases'])==1000
    for p,value in zip(targets[:3],[public,oracle,availability],strict=True):p.write_text(json.dumps(value,indent=2)+'\n')
    receipt={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'parents':40,'queries':200,'panels':1000,'public_views':len(public['views']),
             'pair_scores_computed':0,'output_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in targets[:3]}}
    targets[-1].write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'counts':receipt|{'output_hashes':'sealed'},'availability':availability['query_counts']},indent=2))


if __name__=='__main__':main()
