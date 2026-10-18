"""One immutable extraction into quarantine; never executes package contents."""
from pathlib import Path
from fl_decipher.corpus import digest, dump_json
from fl_decipher.dataset_audit_v15 import unpack, parse_article

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    rows=unpack(ROOT/'data/v15/acquisition/shared_zip/body.bin',ROOT/'data/v15/quarantine')
    for r in rows:
        r['sha256']=digest((ROOT/'data/v15/quarantine'/r['name']).read_bytes())
        r['role']='article_annotation' if r['name'][:2].isdigit() and r['name'][:2]!='00' else ('quarantined_lexicon' if 'LEXICON' in r['name'] else 'index_or_combined_derivative')
    dump_json(ROOT/'data/v15/archive_inventory.json',{'members':rows,'zip_sha256':digest((ROOT/'data/v15/acquisition/shared_zip/body.bin').read_bytes()),'expanded_bytes':sum(r['bytes'] for r in rows),'no_original_source_files':True,'lexicons_used_for_induction':False})
    parsed=[parse_article(p.read_text(encoding='utf-8-sig'),p.name) for p in sorted((ROOT/'data/v15/quarantine').glob('[0-9][0-9]-*.txt')) if p.name[:2]!='00']
    dump_json(ROOT/'data/v15/parsed_annotations.json',{'origin':'Author-provided annotations; not independent source text or semantic gold','articles':parsed})
    print('Articles',len(parsed),'Kamri units',sum(len(x['units']) for x in parsed if x['language']=='Kamri'),'Western units',sum(len(x['units']) for x in parsed if x['language']=='Kamri Western'))
