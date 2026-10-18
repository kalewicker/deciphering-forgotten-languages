"""One immutable run of residual literal-token context evidence."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.residual_context_v27 import evaluate

ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'experiments/kamri_residual_context_v27.json').read_text())
    bench=json.loads((ROOT/'benchmarks/kamri_residual_context_v27.json').read_text())
    pre=json.loads((ROOT/'data/v27/preflight.json').read_text());frozen=json.loads((ROOT/'data/v27/frozen.json').read_text())
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert digest((ROOT/p).read_bytes())==h,p
    out=ROOT/'runs/000027_kamri_residual_context';out.mkdir(exist_ok=False)
    m={'experiment_id':cfg['experiment_id'],'stage':'exposed_residual_literal_context','state':'running','started_at_utc':utc(),
       'model_executed':True,'model_kind':'fixed residual literal-token run matching','translation_model_executed':False,
       'new_lexical_induction_executed':False,'input_hashes':bench['input_hashes']|{'benchmarks/kamri_residual_context_v27.json':digest((ROOT/'benchmarks/kamri_residual_context_v27.json').read_bytes())},'code_hashes':pre['code_hashes']}
    dump_json(out/'manifest.json',m)
    try:
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<=bench['frozen_at_utc']<m['started_at_utc']
        result=evaluate(frozen)
        for key,data in result.items():dump_json(out/(key+'.json'),data)
        summary=[]
        for q,ledger,d in zip(frozen['queries'],result['query_ledgers'],result['decisions'],strict=True):
            expected=next(r for r in ledger['document_rankings'] if r['document_id']==q['expected_page_id'])
            summary.append({'query_id':q['id'],'query_context_tokens':q['token_count'],
                            'best_natural_score':ledger['document_rankings'][0]['score'],
                            'expected_page_score':expected['score'],'natural_qualifying_documents':sum(r['qualifies'] for r in ledger['document_rankings']),
                            'source_work_absent_nomination':d['source_work_absent']['nominated'],
                            'nominated_page_retrieved':d['nominated_page_retrieved']})
        report={'experiment_id':cfg['experiment_id'],'counts':frozen['counts'],'blocked_token_count':len(frozen['blocked_tokens']),
                'query_summary':summary,'gate':result['gate'],
                'expected_pages_retrieved':sum(d['nominated_page_retrieved'] for d in result['decisions']),
                'source_work_absent_nominations':sum(d['source_work_absent']['nominated'] is not None for d in result['decisions']),
                'positive_context_copies_qualified':sum(d['positive_copy_qualifies'] for d in result['decisions']),
                'anchor_frames_qualified':sum(d['anchor_frame_qualifies'] for d in result['decisions']),
                'model_executed':True,'translation_model_executed':False,'new_lexical_induction_executed':False,
                'source_identities_admitted':0,'semantic_labels_admitted':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
                'semantic_evaluation_metrics':None,'primary_gap_lead':None,'target_rescored':False,'new_network_requests':0,
                'limits':['Only literal normalized-token context, not unknown-language translation',
                          'Queries/candidate sources are exposed; two Western queries share one work',
                          'Eight page views stay inside previously nominated windows; no whole-book search',
                          'Nine historical exports are a convenience panel, not representative true negatives',
                          'Raw extraction retains footnote, citation, line-wrap and boundary artifacts',
                          'Failure at eight tokens does not reject translated or paraphrased reuse',
                          'Exact-context copy is an implementation control, not source-identity evidence']}
        dump_json(out/'report.json',report)
        md='# Experiment 27: residual literal-token context\n\n'
        md+=f"Expected pages retrieved: {report['expected_pages_retrieved']}/3. Context-copy positives: {report['positive_context_copies_qualified']}/3. Anchor frames qualifying: {report['anchor_frames_qualified']}/3. Gate: {result['gate']['passed']}.\n\n"
        md+='| Query | Context tokens | Best natural score | Expected page score | Qualified natural documents |\n|---|---:|---|---|---:|\n'
        for s in summary:md+=f"| {s['query_id']} | {s['query_context_tokens']} | {s['best_natural_score']} | {s['expected_page_score']} | {s['natural_qualifying_documents']} |\n"
        md+='\nEvery candidate/control score, raw match and tie is retained. This tests literal-token reuse outside reported anchors; it admits no meaning, source identity, independent review or untouched evaluation.\n'
        (out/'report.md').write_text(md)
        m.update(state='completed',finished_at_utc=utc(),outcome='residual_context_gate_passed' if result['gate']['passed'] else 'residual_context_gate_failed',
                 output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
        dump_json(out/'manifest.json',m)
        print(json.dumps({k:report[k] for k in ['counts','blocked_token_count','query_summary','expected_pages_retrieved','positive_context_copies_qualified','anchor_frames_qualified','gate']},indent=2))
    except Exception as error:
        m.update(state='failed',error=f'{type(error).__name__}: {error}');dump_json(out/'manifest.json',m);raise


if __name__=='__main__':main()
