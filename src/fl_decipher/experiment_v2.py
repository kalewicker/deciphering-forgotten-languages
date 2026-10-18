"""Offline immutable edition ablation with fresh-work evaluation and controls."""
from datetime import datetime,timezone
import json,platform,random,sys,time
from pathlib import Path
from .corpus import digest,dump_json
from .text import sentences
from .alignment_v2 import score_matrices,align_matrix,without_work,edge_metrics


def read(path):return json.loads(path.read_text())

def validate(root,benchmark,cfg):
    if set(cfg['development_groups']) & set(cfg['fresh_groups']):raise ValueError('Source-group leakage')
    for path,sha in benchmark['input_hashes'].items():
        if digest((root/path).read_bytes())!=sha:raise ValueError(f'Input changed after freeze: {path}')
    docs={}
    for key,info in benchmark['documents'].items():
        d=read(root/info['path'])
        if digest(d['text'].encode())!=info['text_sha256'] or d['source_group']!=info['source_group']:raise ValueError('Invalid normalized view')
        raw=Path(d['snapshot']['artifact'])
        if not raw.is_absolute():raw=root/raw
        if digest(raw.read_bytes())!=info['raw_sha256']:raise ValueError('Raw artifact changed')
        docs[key]=d
    seen={}
    for record in benchmark['records']:
        group=record['group'];expected='fresh' if group in cfg['fresh_groups'] else 'development'
        if record['split']!=expected:raise ValueError('Split mismatch')
        for s in sentences(docs[record['fl_id']]['text']):
            if s.text in seen and seen[s.text]!=group:raise ValueError('Duplicate FL sentence across source groups')
            seen[s.text]=group
        for source_id in record['references']:
            if docs[source_id]['source_group']!=group:raise ValueError('Reference belongs to another work')
    if {r['group'] for r in benchmark['records']}!=set(cfg['development_groups']+cfg['fresh_groups']):raise ValueError('Missing selected group')
    return docs


def run(root:Path,run_id:str):
    cfgpath=root/'experiments/kamri_alignment_v2.json';benchpath=root/'benchmarks/kamri_alignment_v2.json'
    cfg,benchmark=read(cfgpath),read(benchpath);docs=validate(root,benchmark,cfg)
    out=root/'runs'/run_id;out.mkdir(parents=True,exist_ok=False)
    manifest={'run_id':run_id,'experiment_id':cfg['experiment_id'],'state':'running','started_at_utc':datetime.now(timezone.utc).isoformat(),
              'python':sys.version,'platform':platform.platform(),'input_hashes':{**benchmark['input_hashes'],str(benchpath.relative_to(root)):digest(benchpath.read_bytes())},
              'code_hashes':{str(p.relative_to(root)):digest(p.read_bytes()) for p in sorted([*(root/'src/fl_decipher').glob('*.py'),*(root/'scripts').glob('*.py'),*(root/'tests').glob('*.py')])},'selected_fresh_denominator':2}
    dump_json(out/'manifest.json',manifest);started=time.monotonic()
    try:
        ss={k:sentences(d['text'],k) for k,d in docs.items()};groups={k:d['source_group'] for k,d in docs.items()}
        source_ids=[k for k in docs if k.startswith('source_')];lexicon=read(root/cfg['lexicon_path'])
        caches={};predictions={}
        for record in benchmark['records']:
            group=record['group'];caches[group]={}
            for source_id in source_ids:
                matrices,p=score_matrices(ss[record['fl_id']],ss[source_id],cfg['baseline'],cfg['lexical_method'],lexicon,cfg['lexicon_rules'])
                caches[group][source_id]=matrices;predictions[group]=p
        dump_json(out/'predictions.json',predictions)
        # Same permutations for both methods and both edition pools.
        rng=random.Random(cfg['seed']);permutations={}
        for r in benchmark['records']:
            orders=[]
            for _ in range(cfg['shuffle_repetitions']):
                order=list(range(len(ss[r['fl_id']])));rng.shuffle(order);orders.append(order)
            permutations[r['group']]=orders
        dump_json(out/'permutations.json',permutations)
        results=[];summaries=[]
        for edition,excluded in [('original','source_gad_johnson'),('johnson','source_gad_seer')]:
            pool=[k for k in source_ids if k!=excluded]
            for method,methodcfg in [('structural',cfg['baseline']),('lexical',cfg['lexical_method'])]:
                rankings={}
                for r in benchmark['records']:
                    rankings[r['group']]=sorted([{'source_id':k,**align_matrix(caches[r['group']][k][method],methodcfg)} for k in pool],key=lambda a:(-a['strength'],a['source_id']))
                negative_max=max(a['strength'] for r in benchmark['records'] if r['split']=='development' for a in rankings[r['group']] if groups[a['source_id']]!=r['group'])
                threshold=negative_max+1e-6
                rows=[]
                for r in benchmark['records']:
                    g=r['group'];ranked=rankings[g];correct=[a for a in ranked if groups[a['source_id']]==g][0]
                    absent=without_work({a['source_id']:a for a in ranked},g,groups)
                    wrong=sorted(absent.values(),key=lambda a:(-a['strength'],a['source_id']))[0]
                    admitted=lambda a:a['strength']>=threshold and a['minimum_links_met']
                    expected=r['references'][correct['source_id']]
                    oracle=edge_metrics(correct['links'],expected)
                    top=ranked[0];topcorrect=groups[top['source_id']]==g
                    retrieval=edge_metrics(top['links'],expected if topcorrect else [])
                    # Keep expected denominator even if source selection is wrong.
                    retrieval['reference_edges']=len(expected);retrieval['recall']=retrieval['correct_edges']/len(expected)
                    shuffled=[]
                    for order in permutations[g]:
                        values=[align_matrix([caches[g][k][method][i] for i in order],methodcfg)['strength'] for k in pool]
                        shuffled.append(max(values))
                    row={'group':g,'split':r['split'],'edition':edition,'method':method,'rankings':ranked,
                         'correct_work_rank':next(i+1 for i,a in enumerate(ranked) if groups[a['source_id']]==g),
                         'top_work_correct':topcorrect,'admitted':admitted(top),'top_strength':top['strength'],
                         'threshold':threshold,'conditional_correct_source_alignment':oracle,'retrieved_alignment':retrieval,
                         'source_absent':{'removed_source_ids':[k for k in pool if groups[k]==g],'top':wrong,'false_admission':admitted(wrong)},
                         'shuffle':{'strengths':shuffled,'exceed_or_equal_observed':sum(v>=top['strength'] for v in shuffled),'denominator':len(shuffled)},'annotation_note':r['note']}
                    rows.append(row);results.append(row)
                fresh=[r for r in rows if r['split']=='fresh'];dev=[r for r in rows if r['split']=='development']
                summaries.append({'edition':edition,'method':method,'threshold':threshold,'candidate_works':len({groups[k] for k in pool}),'candidate_documents':len(pool),
                    'fresh_top1':sum(r['top_work_correct'] for r in fresh),'fresh_selected':2,'fresh_correct_admissions':sum(r['top_work_correct'] and r['admitted'] for r in fresh),
                    'fresh_source_absent_false_admissions':sum(r['source_absent']['false_admission'] for r in fresh),
                    'fresh_retrieved_correct_edges':sum(r['retrieved_alignment']['correct_edges'] for r in fresh),
                    'fresh_retrieved_proposed_edges':sum(r['retrieved_alignment']['proposed_edges'] for r in fresh),'fresh_reference_edges':sum(r['retrieved_alignment']['reference_edges'] for r in fresh),
                    'development_top1':sum(r['top_work_correct'] for r in dev),'development_selected':5})
                print(edition,method,'completed',flush=True)
        report={'summaries':summaries,'results':results,'annotation':benchmark['annotation'],'new_lexical_claims':0,'limitations':['Two selected fresh works only','Indexed FL excerpts, not raw/current full pages','Known-source packet ranking with uneven candidate scopes','One analyst structural audit, no semantic gold','Frozen function-word anchors may match unrelated text','Unchanged simple sentence boundaries and 1:1 alignment','Thresholds derived from development negatives; not calibrated guarantees']}
        dump_json(out/'report.json',report)
        lines=['# Experiment 2: source editions and frozen lexical anchors','', 'Exploratory engineering evidence; no validated translation accuracy.','', '| Gad edition | Method | Fresh top-1 / selected | Correct admissions | Fresh absent false admissions | Correct / proposed / reference edges | Dev top-1 |','|---|---|---:|---:|---:|---:|---:|']
        for s in summaries:lines.append(f"| {s['edition']} | {s['method']} | {s['fresh_top1']}/2 | {s['fresh_correct_admissions']}/2 | {s['fresh_source_absent_false_admissions']}/2 | {s['fresh_retrieved_correct_edges']}/{s['fresh_retrieved_proposed_edges']}/{s['fresh_reference_edges']} | {s['development_top1']}/5 |")
        lines+=['','All v1 groups are development data. Source ranking uses seven works in each edition pool; new English inputs are nominated source packets, old inputs retain their broader scopes. Rankings and controls receive no reference links. Each method/pool uses the maximum wrong-work strength on development groups plus 1e-6 as admission threshold.','', '## Detailed outcomes','', '| Edition | Method | Group | Split | Rank | Admitted | Correct-source edges | Absent false admission | Shuffle ≥ observed |','|---|---|---|---|---:|---|---:|---|---:|']
        for r in results:
            m=r['conditional_correct_source_alignment'];sh=r['shuffle'];lines.append(f"| {r['edition']} | {r['method']} | {r['group']} | {r['split']} | {r['correct_work_rank']} | {r['admitted']} | {m['correct_edges']}/{m['reference_edges']} | {r['source_absent']['false_admission']} | {sh['exceed_or_equal_observed']}/{sh['denominator']} |")
        lines+=['','## Interpretation boundaries','',benchmark['annotation'],'','Fresh references retain 15 structural edges across 13 FL sentences. Two Larsen FL sentences split across source sentence boundaries; two hymn FL sentences share one source sentence. A 1:1 aligner cannot recover all these edges. This is measured rather than repaired after observing outcomes.','', 'The lexicon is the exact v1 artifact. No new token claims are induced. Lexical agreement is multiset overlap over emitted frozen candidates; absent predictions are neutral. Reported shuffle exceedances are descriptive, not inferential p-values.','', '## Limitations','']+['- '+v for v in report['limitations']]
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        manifest.update(state='completed',elapsed_seconds=time.monotonic()-started,finished_at_utc=datetime.now(timezone.utc).isoformat(),summaries=summaries,
            output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
        dump_json(out/'manifest.json',manifest)
    except Exception as exc:
        manifest.update(state='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started);dump_json(out/'manifest.json',manifest);raise
    return out
