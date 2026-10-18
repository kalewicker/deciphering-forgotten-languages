"""One pass over fixed requests and at most two metadata-derived dated replays."""
from pathlib import Path
import argparse
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.capture_review_v23 import request, skipped, select_archive

ROOT = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--diagnostic-route');args = parser.parse_args()
    cp = ROOT/'experiments/kamri_capture_review_v23.json';cfg = read(cp)
    for p, sha in cfg['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    out = ROOT/'data/v23/acquisition'
    if args.diagnostic_route:
        key = args.diagnostic_route
        old = read(out/key/'receipt.json')
        assert old['attempted'] and old['curl_returncode'] in (6, 7)
        assert old['curl_returncode'] == 6 or any(s in old['stderr'].lower() for s in ['permission denied', 'operation not permitted'])
        result = request(out, key+'_diagnostic', old['requested_url'], cfg['request_limits'], old['kind'])
        print(key+'_diagnostic', 'HTTP', result['http_status'], 'curl', result['curl_returncode'], flush=True)
        return
    out.mkdir(exist_ok=False)
    for n in cfg['nominees']:
        for kind, url in [('native', n['fl_url']), ('source', n['source_url']), ('metadata', n['cdx_url'])]:
            key = n['id']+'_'+kind
            print('Fetching', key, flush=True)
            result = request(out, key, url, cfg['request_limits'], kind)
            print(key, 'HTTP', result['http_status'], 'curl', result['curl_returncode'], flush=True)
        meta = read(out/(n['id']+'_metadata')/'receipt.json')
        body = out/(n['id']+'_metadata')/'body.bin'
        selection = select_archive(body.read_bytes(), n) if meta['transport_complete'] else {'eligible': False, 'reason': 'metadata_transport_unavailable', 'record': None, 'replay_url': None}
        dump_json(out/(n['id']+'_archive_selection.json'), selection)
        key = n['id']+'_archive'
        if selection['eligible']:
            print('Fetching', key, flush=True)
            result = request(out, key, selection['replay_url'], cfg['request_limits'], 'archive')
            print(key, 'HTTP', result['http_status'], 'curl', result['curl_returncode'], flush=True)
        else:
            skipped(out, key, 'archive', selection['reason']);print(key, 'not attempted:', selection['reason'], flush=True)

if __name__ == '__main__':
    main()
