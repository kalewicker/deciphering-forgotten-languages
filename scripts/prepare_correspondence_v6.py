"""Save fixed within-article blocks and structural references before scoring."""
import json
from pathlib import Path

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.register_v5 import audit_aliases
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://forgottenlanguages-full.forgottenlanguages.org/2019/09/misinfons-and-hypermemetic-logic.html'
BLOCKS = {
    'continuation': '''Vaċnir, maksu, walmlir tafliġ fakċnin kińńir, kidċdan deir datlir şo fafvam tagvah daċċęį ramsam vaċsiġ mişthi gańrdir fafvam rawe ńu tawwdan an dagkiġ ńańi mavsdin misrdir mivvdir kaflhi talsiţ kiwvlir. Mişthi kidċdan safdu nafnnin nesşlir, vaċsiġ, tawwdan şu gavşlar ńańi mavsdin mivre ċe netre şo fafvam şu nafwi nesvhi vaċdęį ńu şu mirge rawklar:''',
    'mechanism': '''Şu datrlar ńańi şu şoaš wasşa kirwdan mavsdin nadgah du milsaš şo şu kiċsdar tawfiţ cybermagic. Kańşaš şo navvo nadge, cybermagic kidċdan deir raktiġ ċu misre vaffdar şo dagńęį ċeaš kikşlir. Rańki, şu misriġ daglam kikkdir ċoiš neċte miswam miwnam fadmdin, nalńi fasręį daċċęįš tańċaš navńaķ vaċse ńańi şu tatni nefsdan. Şu katwdir mavsdin şi vaċńiţ gańńah şdaċċęį daċċęįš vaftaķ newtu sanńaš şo daċċęį kaşaš gasko ċu daċċęį gau. Şu kaşaš gasko darlir magńi lasddin miċşdin şoaš şu mavsdin (deir mańvu mivgnin) şi deir dagnęį miro ńu şu nesdlar, şoaš kimgam warah fafvam, ńo rańki şi kigńnin:''',
}


def main():
    benchpath = ROOT/'benchmarks/kamri_correspondence_v6.json'
    cfgpath = ROOT/'experiments/kamri_correspondence_v6.json'
    if benchpath.exists() or cfgpath.exists():
        raise ValueError('Preserve existing input freeze')
    old = json.loads((ROOT/'benchmarks/kamri_register_v5.json').read_text())
    cfg = json.loads((ROOT/'experiments/kamri_register_v5.json').read_text())
    for k in ('development_groups', 'fresh_groups'):
        cfg.pop(k)
    cfg.update(experiment_id='kamri_correspondence_v6', registration='experiments/kamri_correspondence_v6.md',
               variants=['baseline', 'gated_aliases'], seed=6831,
               thresholds=json.loads((ROOT/'runs/000005_kamri_scoped_register/report.json').read_text())['thresholds'])
    cfg['thresholds'] = {k: cfg['thresholds'][k] for k in cfg['variants']}
    documents = {k: v for k, v in old['documents'].items() if k in cfg['candidate_ids']}
    opening = next(r for r in old['records'] if r['group'] == 'models_magic')
    documents[opening['fl_id']] = old['documents'][opening['fl_id']]
    records = [{**opening, 'packet': 'opening', 'split': 'development_audit'}]
    source = json.loads((ROOT/documents['source_models_magic']['path']).read_text())
    sa = sentences(source['text'])
    ledger = {'fl_url': URL, 'raw_page_status': 'unavailable',
              'raw_page_attempt': 'Direct web open failed with non-retryable HTTP 500/captcha redirect; no bypass or repeat direct fetch.',
              'indexed_status': 'imported_selection', 'inspection_date': '2026-09-30',
              'index_locator': 'Exact URL-restricted cybermagic search; returned full indexed article, crawled about three months earlier.',
              'selected_blocks': [], 'independent_fl_articles': 1, 'independent_source_works': 1,
              'independent_fresh_works': 0, 'unavailable_altruist_source': 'unchanged; outside this audit'}
    for packet, text in BLOCKS.items():
        key = 'fl_models_magic_'+packet+'_v6'
        path = ROOT/'data/normalized'/f'{key}.json'
        if path.exists():
            raise ValueError(f'Preserve {path}')
        assert len(text.split()) <= 180 and text.endswith(':')
        receipt = snapshot(ROOT/'data/raw', URL, content=text.encode(), acquisition_kind='indexed_web_excerpt',
                           locator=f'Selected {packet} block only; exact indexed text; colon before embedded English quotation. No raw HTTP body claim.')
        doc = normalized_document(key, receipt, text, kind='fl', group='models_magic',
                                  transformations=['Verbatim selected Kamri-only block; stop before embedded English quote; no drop-cap or spelling repairs'])
        dump_json(path, doc)
        fa = sentences(text)
        start = 64 if packet == 'continuation' else 66
        assert len(fa) == (2 if packet == 'continuation' else 5)
        edges = [{'fl_index': i, 'source_index': start+i, 'fl_span': [f.start, f.end],
                  'source_span': [sa[start+i].start, sa[start+i].end],
                  'state': 'single_analyst_structural_correspondence', 'semantic_gold': False} for i, f in enumerate(fa)]
        documents[key] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes()),
                          'text_sha256': doc['text_sha256'], 'raw_sha256': receipt['sha256'], 'source_group': 'models_magic'}
        records.append({'packet': packet, 'group': 'models_magic', 'split': 'within_article_check',
                        'fl_id': key, 'source_id': 'source_models_magic', 'available': True, 'edges': edges,
                        'note': 'Separate original block ending at a colon before an English quotation. Ordered structural labels only; unknown token meanings unaudited.'})
        ledger['selected_blocks'].append({'packet': packet, 'fl_atoms': len(fa), 'whitespace_words': len(text.split()),
            'right_boundary': 'embedded English quotation excluded',
            'quotation_locator': 'meme/misinfon definition' if packet == 'continuation' else 'cultural information quotation',
            'left_boundary': 'after opening morphic-fields statement' if packet == 'continuation' else 'after meme/misinfon English quotation',
            'source_atoms': list(range(start, start+len(fa))), 'raw_receipt': receipt})
    annotations = []
    for r in records:
        fl = json.loads((ROOT/documents[r['fl_id']]['path']).read_text())
        fa = sentences(fl['text'])
        rows = []
        for i, f in enumerate(fa):
            ids = sorted({e['source_index'] for e in r['edges'] if e['fl_index'] == i})
            rows.append({'fl_index': i, 'fl_span': [f.start, f.end], 'fl_text': f.text,
                         'source_indices': ids, 'source_spans': [[sa[j].start, sa[j].end] for j in ids],
                         'source_text': ' '.join(sa[j].text for j in ids),
                         'reference_basis': 'Ordered parallel prose and named literal anchors; single analyst; semantic meanings unavailable',
                         'semantic_gold': False})
        annotations.append({'packet': r['packet'], 'correspondences': rows,
                            'aliases': audit_aliases(fl['text'], source['text'], r['edges'])})
    dump_json(ROOT/'benchmarks/inputs/correspondence_v6_acquisition.json', ledger)
    dump_json(ROOT/'benchmarks/inputs/correspondence_v6_annotations.json', {
        'independent_source_works': 1, 'semantic_gold': False, 'new_supported_lexical_entries': 0,
        'editorial_notes': [
            'Opening contains hipermemetik mirde where the source topic is magic; no semantic gloss asserted.',
            'Source opening has literal date 1987; the selected FL opening contains no numeric date.',
            'The source premises and e.g. split are retained as the existing multi-edge labels.',
            'The new block boundaries end at colons where source atoms 65 and 70 end with periods.',
            'Cybermagic is literal shared text. Source parenthetical English definitions and MS-DOS literal spelling differ; unknown FL replacements/omissions are not resolved.',
        ], 'packets': annotations})
    dump_json(cfgpath, cfg)
    paths = [v['path'] for v in documents.values()] + [cfg['registration'], str(cfgpath.relative_to(ROOT)),
        cfg['lexicon_path'], 'benchmarks/kamri_register_v5.json', 'runs/000005_kamri_scoped_register/report.json',
        'benchmarks/inputs/correspondence_v6_acquisition.json', 'benchmarks/inputs/correspondence_v6_annotations.json',
        'pyproject.toml', 'uv.lock']
    raw = {}
    for key, info in documents.items():
        d = json.loads((ROOT/info['path']).read_text())
        raw[d['snapshot']['artifact']] = info['raw_sha256']
    benchmark = {'schema_version': 6, 'status': 'frozen_before_model_execution', 'selected_within_article_denominator': 2,
                 'independent_source_works': 1, 'fresh_independent_works': 0, 'documents': documents, 'records': records,
                 'input_hashes': {p: digest((ROOT/p).read_bytes()) for p in paths}, 'raw_acquisition_hashes': raw}
    dump_json(benchpath, benchmark)
    print('Frozen opening + two within-article blocks; no independent fresh work; ten unchanged candidates.')
    print(json.dumps(ledger['selected_blocks'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
