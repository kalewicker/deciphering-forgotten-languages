"""One immutable structural audit; all uncertain mappings remain in the outputs."""
from pathlib import Path
from collections import Counter
import html,json,bs4,unicodedata
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.block_audit_v28 import html_map,pdf_map,fl_reference,source_reference,summarize

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads((ROOT/p).read_text())
def preview(text):return '<code>'+html.escape(text[:200].replace('\n',' ⏎ ')).replace('|','&#124;')+'</code>'


def main():
    cfg=read('experiments/kamri_block_audit_v28.json');pre=read('data/v28/preflight.json');bench=read('benchmarks/kamri_block_audit_v28.json')
    assert bs4.__version__==cfg['beautifulsoup_version'] and unicodedata.unidata_version==cfg['unicode_version']
    for hashes in [bench['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert digest((ROOT/p).read_bytes())==h,p
    out=ROOT/'runs/000028_kamri_block_audit';out.mkdir(exist_ok=False)
    m={'experiment_id':cfg['experiment_id'],'stage':'structural_boundary_coverage_audit','state':'running','started_at_utc':utc(),
       'model_executed':False,'input_hashes':bench['input_hashes']|{'benchmarks/kamri_block_audit_v28.json':digest((ROOT/'benchmarks/kamri_block_audit_v28.json').read_bytes())},'code_hashes':pre['code_hashes']}
    dump_json(out/'manifest.json',m)
    try:
        assert cfg['registered_at_utc']<pre['sealed_at_utc']<bench['frozen_at_utc']<m['started_at_utc']
        geometry=read('data/v28/pdf_geometry.json');assert geometry['state']=='completed' and len(geometry['pages'])==8
        raw_pages={p['id']:p for p in read('data/v27/page_views.json')['pages']}
        fl_maps={};pdf_maps=[];exports={};legacy={}
        for work in cfg['works']:
            key=work['id'];exports[key]=(ROOT/work['fl_export']).read_text();legacy[key]=(ROOT/work['legacy_source']).read_text()
            fl_maps[key]=html_map((ROOT/work['archive_html']).read_bytes(),exports[key])
        for page in geometry['pages']:
            pdf_maps.append(pdf_map(page,raw_pages[page['id']]['text'],legacy[page['work']]))
        appendix=read('data/v26/evidence_spans.json');queries=read('data/v27/frozen.json')['queries'];fl_refs=[];source_refs=[]
        for r in appendix['pairs']+appendix['unmatched_english_blocks']:
            ref={'reference_id':r['id'],'kind':'appendix_pair' if 'source_span' in r else 'reported_english_block','work':r['packet'],'span':r['fl_span']}
            fl_refs.append(fl_reference(ref,fl_maps[r['packet']],exports[r['packet']]))
            if 'source_span' in r:
                source_refs.append(source_reference({'reference_id':r['id'],'work':r['packet'],'span':r['source_span'],'reported_pdf_page':r['pdf_page']},pdf_maps,legacy[r['packet']]))
        for q in queries:
            ref={'reference_id':'v27:'+q['id'],'kind':'v27_context','work':q['packet'],
                 'span':{'start':q['fl_char_start'],'end':q['fl_char_end'],'text':q['text']}}
            fl_refs.append(fl_reference(ref,fl_maps[q['packet']],exports[q['packet']]))
        summary=summarize(fl_maps,pdf_maps,fl_refs,source_refs)
        for name,data in [('html_maps',fl_maps),('pdf_maps',pdf_maps),('fl_references',fl_refs),('source_references',source_refs),('summary',summary)]:dump_json(out/(name+'.json'),data)
        derived=ROOT/'data/v28/maps';derived.mkdir(exist_ok=False)
        for key,mapping in fl_maps.items():
            md=f'# Parsed HTML block runs: {key}\n\nOriginal export offsets are unchanged. Roles describe markup only; link-only and emphasis are not bibliography/navigation labels. Full strings and DOM paths are in the JSON map.\n\n'
            md+='| Run | Export span | Markup role | Link only | Preview |\n|---|---|---|---|---|\n'
            for b in mapping['blocks']:md+=f"| {b['block_id']} | [{b['start']},{b['end']}) | {b['role']} | {b['link_only']} | {preview(b['text'])} |\n"
            (derived/(key+'_html.md')).write_text(md)
        md='# PDF layout and export concordance\n\nGeometry roles are candidate hints. Missing/ambiguous line matches are retained, not corrected. These are normalized-token concordances with exact raw target spans in the JSON map.\n'
        for page in pdf_maps:
            row=raw_pages[page['page_id']];md+=f"\n## {page['page_id']}\n\n![Unchanged source page](../../{row['image'].removeprefix('data/')})\n\n"
            md+='| Line | Hint | Raw-page status | Legacy status | Preview |\n|---|---|---|---|---|\n'
            for line in page['lines']:
                md+=f"| {line['line_id'].rsplit(':',1)[1]} | {line['role_hint']} | {line['raw_page_concordance']['status']} | {line['legacy_window_concordance']['status']} | {preview(line['text'])} |\n"
        (derived/'pdf_layout.md').write_text(md)
        integrity={'two_exact_FL_reconstructions':len(fl_maps)==2 and all(f['exact_reconstruction'] for f in fl_maps.values()),
                   'two_exact_FL_partitions':all(f['exact_partition'] for f in fl_maps.values()),'all_eight_pages_mapped':len(pdf_maps)==8,
                   'all_words_assigned_once':all(p['all_words_assigned_once'] for p in pdf_maps),'all_reference_spans_valid':len(fl_refs)==16 and len(source_refs)==9}
        assert all(integrity.values())
        report={'experiment_id':cfg['experiment_id'],'engineering_integrity':integrity,'engineering_integrity_passed':all(integrity.values()),
                'summary':summary,'scientific_acceptance':None,'model_executed':False,'source_identities_admitted':0,
                'semantic_labels_admitted':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
                'semantic_evaluation_metrics':None,'target_rescored':False,'new_network_requests':0,
                'limits':['DOM paths refer to the registered parsed/filtered DOM, not raw byte offsets or browser layout',
                          'No semantic paragraph roles, language labels or cross-language alignment inferred',
                          'Geometry roles are candidates; ambiguous/unmapped normalized-token concordances retained',
                          'Line mapping absence is not proof of text deletion or semantic absence',
                          'Citation inventory covers only bracketed comma-separated numeric markers',
                          'All earlier failed gates and uncertain hypotheses remain unchanged']}
        dump_json(out/'report.json',report)
        (out/'report.md').write_text('# Audit 28: block boundaries and export coverage\n\n'
            +f'Engineering integrity: {report["engineering_integrity_passed"]}. Two exact FL reconstructions, eight mapped pages, sixteen FL references and nine legacy-source reference maps.\n\n'
            +'All atom/separator spans, candidate geometry roles, unique/ambiguous/unmapped line occurrences and citation markers are retained. No source/semantic acceptance or translation evaluation occurs.\n')
        m.update(state='completed',finished_at_utc=utc(),outcome='structural_maps_complete_semantic_acceptance_unchanged',
                 input_hashes=m['input_hashes']|{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in derived.rglob('*') if p.is_file()},
                 output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
        dump_json(out/'manifest.json',m)
        print(json.dumps({'engineering_integrity':integrity,'summary':summary},indent=2))
    except Exception as error:
        m.update(state='failed',error=f'{type(error).__name__}: {error}');dump_json(out/'manifest.json',m);raise


if __name__=='__main__':main()
