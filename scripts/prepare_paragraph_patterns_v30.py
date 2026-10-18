"""Freeze registry, controls and every null order without computing scores."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,html,json
from fl_decipher.paragraph_patterns_v30 import registry,control,null_order

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())


def main():
    cfg=read('experiments/paragraph_patterns_v30.json');pre=read('data/v30/preflight.json')
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for name,h in hashes.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    target=ROOT/'data/v30/frozen.json';assert not target.exists()
    units=registry(read('runs/000028_kamri_block_audit/html_maps.json'),read('runs/000028_kamri_block_audit/pdf_maps.json'),
                   read('runs/000029_risk_layout_derivative/pages.json'),cfg,read('data/v26/frozen.json')['queries'])
    controls=[control(q,kind)|{'query_id':q['id']} for q in units['queries'] for kind in ['opaque','anchor_frame','reverse']]
    candidates=[u for u in units['source_units'] if u['candidate']]
    draws=[{'draw':d,'orders':{u['unit_id']:null_order(u,d) for u in candidates}} for d in range(cfg['null_draws'])]
    frozen={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'registry':units,'controls':controls,'null_orders':draws}
    target.write_text(json.dumps(frozen,indent=2,ensure_ascii=False)+'\n')
    md='# Frozen paragraph/source-unit registry v30\n\nAll roles are exposed editorial or markup observations. Full exact strings, tokens, blocked positions and source-piece links are in frozen.json. Only the three registered FL paragraphs are queries. Source fragments are not joined across pages.\n\n'
    for key in ['fl_units','source_units']:
        md+=f'## {key}\n\n| Unit | Role | Candidate | Source location | Preview |\n|---|---|---|---|---|\n'
        for u in units[key]:
            loc=str([u['original_start'],u['original_end']]) if key=='fl_units' else str(u['line_indices'])
            preview=html.escape(u['text'][:180]).replace('|','&#124;').replace('\n',' ⏎ ')
            md+=f"| {u['unit_id']} | {u['role']} | {u.get('candidate','query selection separate')} | {loc} | <code>{preview}</code> |\n"
        md+='\n'
    (ROOT/'data/v30/units.md').write_text(md)
    print(json.dumps({'FL_units':len(units['fl_units']),'source_units':len(units['source_units']),'source_candidates':len(candidates),'queries':len(units['queries']),'blocked_forms':len(units['blocked_forms']),'null_panels':len(draws)}))


if __name__=='__main__':main()
