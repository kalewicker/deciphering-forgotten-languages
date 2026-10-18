"""One frozen source-layout derivative; no previous experiment is rescored."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,html,json
from fl_decipher.risk_layout_v29 import assemble,continuities,engineering_gate

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def main():
    cfg=read('experiments/risk_layout_derivative_v29.json');pre=read('data/v29/preflight.json');bench=read('benchmarks/risk_layout_derivative_v29.json')
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert sha(p)==h,p
    out=ROOT/'runs/000029_risk_layout_derivative';out.mkdir(exist_ok=False)
    manifest={'experiment_id':cfg['experiment_id'],'state':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),
              'input_hashes':bench['input_hashes']|{'benchmarks/risk_layout_derivative_v29.json':sha('benchmarks/risk_layout_derivative_v29.json')},'code_hashes':pre['code_hashes']}
    write(out/'manifest.json',manifest)
    try:
        primitive=read('data/v29/primitives.json')
        assert primitive['state']=='completed' and len(primitive['pages'])==3
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<primitive['extracted_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']
        raw={p['id']:p for p in read('data/v27/page_views.json')['pages']}
        legacy=(ROOT/cfg['legacy_source']).read_text()
        pages=[assemble(p,raw[p['id']]['text'],legacy) for p in primitive['pages']]
        continuity=continuities(pages);gate=engineering_gate(pages,continuity)
        summary=[]
        for p,source in zip(pages,primitive['pages'],strict=True):
            summary.append({'page_id':p['page_id'],'glyphs':len(source['chars']),'native_code_points':len(p['native_glyph_text']),
                            'derivative_code_points':len(p['text']),'lines':len(p['lines']),
                            'inferred_spaces':sum(v['kind']=='inferred_space' for v in p['pieces']),
                            'role_hints':dict(Counter(l['role_hint'] for l in p['lines'])),
                            'raster_rule_candidates':len(p['raster_rules']),
                            'raw_mapping_status':dict(Counter(l['raw_page_concordance']['status'] for l in p['lines'])),
                            'legacy_mapping_status':dict(Counter(l['legacy_window_concordance']['status'] for l in p['lines'])),
                            'raw_citation_keys':dict(Counter(c['key'] for c in p['raw_numeric_citations'])),
                            'derivative_citation_keys':dict(Counter(c['key'] for c in p['derivative_numeric_citations']))})
            (out/f"risk_math_{p['pdf_page_one_based']:03d}.txt").write_text(p['text'])
        old=[p for p in read('runs/000028_kamri_block_audit/summary.json')['pdf_pages'] if p['page_id'].startswith('risk_math:')]
        report={'experiment_id':cfg['experiment_id'],'engineering_components':gate,'automatic_engineering_gate_passed':all(gate.values()),
                'visual_QA_required':True,'summary':summary,'v28_descriptive_baseline':old,'denominators_changed':True,
                'scientific_acceptance':None,'semantic_evaluation_metrics':None,'semantic_labels_admitted':0,'source_identities_admitted':0,
                'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'model_executed':False,'target_rescored':False,'new_network_requests':0}
        for name,value in [('pages',pages),('continuities',continuity),('report',report)]:write(out/(name+'.json'),value)
        md='# Risk character-layout derivative v29\n\nExposed engineering fixture; role hints are provisional. Every glyph, inferred space and newline has an exact piece record in pages.json. Native glyph offsets are distinct from saved pypdf and legacy offsets. Original citation digits, spelling and hyphenation are preserved.\n'
        for p,spec in zip(pages,cfg['pages'],strict=True):
            md+=f"\n## PDF page {p['pdf_page_one_based']}\n\n![Unchanged source page](../../{spec['image']})\n\n"
            md+='| Line | Role hint | Raw match | Legacy match | Full derivative line |\n|---|---|---|---|---|\n'
            for line in p['lines']:
                text=html.escape(line['text']).replace('|','&#124;').replace('\n',' ⏎ ')
                md+=f"| {line['line_id'].rsplit(':',1)[1]} | {line['role_hint']} | {line['raw_page_concordance']['status']} | {line['legacy_window_concordance']['status']} | <code>{text}</code> |\n"
        (out/'layout_review.md').write_text(md)
        manifest.update(state='completed',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='automatic_engineering_gate_passed_visual_QA_pending' if all(gate.values()) else 'engineering_gate_failed_preserved',
                        output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='manifest.json'})
        write(out/'manifest.json',manifest)
        print(json.dumps(report,indent=2))
    except Exception as error:
        manifest.update(state='failed',error=f'{type(error).__name__}: {error}');write(out/'manifest.json',manifest);raise


if __name__=='__main__':main()
