"""One immutable execution of preregistered development anchor specificity."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.source_specificity_v26 import evaluate

ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'experiments/kamri_source_specificity_v26.json').read_text())
    benchmark=json.loads((ROOT/'benchmarks/kamri_source_specificity_v26.json').read_text())
    pre=json.loads((ROOT/'data/v26/preflight.json').read_text())
    for hashes in [benchmark['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert digest((ROOT/p).read_bytes())==h,p
    frozen=json.loads((ROOT/benchmark['frozen_inputs']).read_text())
    out=ROOT/'runs/000026_kamri_source_specificity';out.mkdir(exist_ok=False)
    m={'experiment_id':cfg['experiment_id'],'stage':'exposed_development_anchor_specificity','state':'running','started_at_utc':utc(),
       'model_executed':True,'model_kind':'fixed ordered-anchor retrieval','translation_model_executed':False,
       'new_lexical_induction_executed':False,'code_hashes':pre['code_hashes'],
       'input_hashes':benchmark['input_hashes']|{'benchmarks/kamri_source_specificity_v26.json':digest((ROOT/'benchmarks/kamri_source_specificity_v26.json').read_bytes())}}
    dump_json(out/'manifest.json',m)
    try:
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<=benchmark['frozen_at_utc']<m['started_at_utc']
        result=evaluate(frozen)
        dump_json(out/'query_ledgers.json',result['query_ledgers']);dump_json(out/'primary_decisions.json',result['primary_decisions'])
        dump_json(out/'control_scores.json',result['control_scores']);dump_json(out/'gate.json',result['gate'])
        report={'experiment_id':cfg['experiment_id'],'stage':m['stage'],'counts':frozen['counts'],'appendix_audit':frozen['appendix_audit'],
                'natural_localizations':sum(r['natural_localizes_nominee'] for r in result['primary_decisions']),
                'source_absent_natural_nominations':sum(r['source_absent_natural_nomination'] for r in result['primary_decisions']),
                'source_absent_frame_false_nominations':sum(r['source_absent_frame_false_nomination'] for r in result['primary_decisions']),
                'natural_window_scores':sum(len(r['window_scores']) for r in result['query_ledgers']),
                'primary_decisions':result['primary_decisions'],'gate':result['gate'],
                'source_identity_claims_admitted':0,'semantic_labels_admitted':0,'independent_reviews_admitted':0,
                'untouched_test_units_admitted':0,'semantic_evaluation_metrics':None,'target_rescored':False,'primary_gap_lead':None,
                'model_executed':True,'translation_model_executed':False,'new_lexical_induction_executed':False,'new_network_requests':0,
                'limits':['All sources and observed queries are exposed development material',
                          'Eleven historical source exports do not represent the web or independent true negatives',
                          'Western contributes two dependent primary clusters; two positive works total',
                          'Synthetic frames test identifiability, not the prevalence of fabricated sources',
                          'Same-work alternatives outside saved excerpts are not included',
                          'Exact English-block absence is not absence of semantic counterparts',
                          'No meanings, independent review, direct-source identity or untouched validation admitted']}
        dump_json(out/'report.json',report)
        md='# Experiment 26: restricted-corpus ordered-anchor specificity\n\n'
        md+=f"Natural localizations: {report['natural_localizations']}/3; source-absent natural nominations: {report['source_absent_natural_nominations']}/3; copied-frame false nominations: {report['source_absent_frame_false_nominations']}/3. Combined gate: {result['gate']['passed']}.\n\n"
        md+='| Primary cluster | Natural nomination | Source absent | Source plus frame | Source absent plus frame |\n|---|---|---|---|---|\n'
        for r in result['primary_decisions']:
            md+='| '+r['query_id']+' | '+' | '.join(str(r['decisions'][k]['nominated']) for k in ['natural','source_absent','source_present_plus_frame','source_absent_plus_frame'])+' |\n'
        md+='\nAll six queries, every natural window, all ten control views and twelve primary decisions are retained. Positive-work denominator is two; the three clusters are not independent works. No source identity, semantic labels, independent review or untouched-test admission occurs.\n'
        (out/'report.md').write_text(md)
        m.update(state='completed',finished_at_utc=utc(),outcome='restricted_gate_passed' if result['gate']['passed'] else 'source_specificity_gate_failed',
                 output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
        dump_json(out/'manifest.json',m)
        print(json.dumps({k:report[k] for k in ['natural_localizations','source_absent_natural_nominations','source_absent_frame_false_nominations','natural_window_scores','gate']},indent=2))
    except Exception as error:
        m.update(state='failed',error=f'{type(error).__name__}: {error}');dump_json(out/'manifest.json',m);raise


if __name__=='__main__':main()
