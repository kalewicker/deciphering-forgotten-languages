"""Read-only check of a new return; no packet modification or label admission."""
import argparse
import json
from pathlib import Path
from fl_decipher.review_handoff_v25 import encoded,sha,validate_return

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nominee',choices=['western_esoterism','risk_math'])
    parser.add_argument('return_file',type=Path)
    args=parser.parse_args()
    packet=ROOT/'data/v25/packets'/args.nominee
    raw=(packet/'material_manifest.json').read_bytes();manifest=json.loads(raw)
    run=json.loads((ROOT/'runs/000025_kamri_review_handoff/report.json').read_text())
    expected=next(r['manifest_sha256'] for r in run['records'] if r['nominee_id'] == args.nominee)
    assert sha(raw) == expected,'packet manifest changed'
    for name,record in manifest['members'].items():
        assert sha((packet/name).read_bytes()) == record['sha256'],name
    raw_return=args.return_file.read_bytes()
    value=json.loads(raw_return)
    result=validate_return(value,manifest,sha(raw),
        {'fl':(packet/'fl_post.txt').read_text(),'source':(packet/'publisher_window.txt').read_text()})
    result['return_sha256']=sha(raw_return);result['packet_manifest_sha256']=sha(raw)
    print(encoded(result).decode(),end='')
    raise SystemExit(0 if result['structurally_valid'] else 2)


if __name__ == '__main__':
    main()
