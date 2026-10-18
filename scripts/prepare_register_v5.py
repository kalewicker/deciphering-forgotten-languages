"""Finite saved-source preparation, development audit, and fresh text selection."""
import json
from pathlib import Path
import re
import shutil

from fl_decipher.corpus import digest, dump_json, normalized_document, snapshot
from fl_decipher.register_v5 import audit_aliases
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
FL = {
    'capra_foreword': ('https://forgottenlanguages-full.forgottenlanguages.org/2019/07/reality-and-other-mental-devices-on.html', '''Ńu nadka negrnin, şu daşdęį ńi gawnlir du ratknin ńu newgdir daşviţ şa şu nesdah ńi dańtu aš miwńiţ. Şu radah ve malċa gawnlir kavldan, şo daċċęį miktu kitkdin, şu netşah ńi şu nasńi faċno negfam du ladrlir negrlir şo dafklar şu dańċdir ve şu daşldir kartesianir daċvaš ċu dańrlir aš mivsdan, ċu şu nasşam aš şu nasńi, ċeiš dańthi mirgiš da mitċęį. Ńu faċno negrnin, wakşlar ċeiš namnlir taċşiţ doaš nalmdin şiaš, şair şu daşgu daşwir, taċşo doaš navwlir. Şu nenkdan lafkdan ńi newgdir daşviţ, wańċęį ńu saşdah ńu vaċęį daċsaķ şo daċsaķ ramwęį, kidċdan deir rafrdin şo şu dańrlir ńi şu nasşam kitńhi. Maksu, sagwdir negrlir dańfi daċmdan şo daşki gawnlir şoaš kirda dawnęį ńi şu vatfiţ aš dańfi davmiš ve wakşlar dańraš da fanńlar ċa lalċiš nesram ńu ńo varldir ńi dańtęį negfam dań wakşlar miċşaķ ċu doaš mişthi. Vańgdin, şu daşdęį ńi şu nalmdin ńi gawnlir du daċmdan ńi şu ladto ńi saşdaķ ramwęį, daċwnin ńu şu dańtęį saşam:'''),
    'accidental_altruist': ('https://forgottenlanguages-full.forgottenlanguages.org/2019/07/altruistic-beacons-exotic-altruistic.html', '''Ş u daċċiġ ńi siknalńi şi miċsęį şoaš daċċiġ ńi dannaķ, şo mavsęį dańvlar galvdan ńi şu siknalċa dańċa. M aksu, şu samslir dańraš kaċmiġ daċċęį miwwi katvlar şo manslar daşndin fakllar şo şu raaķ, dańviġ mişthi naċvlir da miċsęį şo mańfa şu raşwu. Nefgam mişthi di miwńa şoaš daċċęį misdi şo kinċlir dańvlar galvdan şo kisvnin samtir ranmhi faċtir şo kaċmah aš wadse şu siknal, kişńaš şu raşwu galvah aš milram vaċńam wafli şo daċşdan. Dańviġ nefgam mişthi di miwńa şo vańşdir şu galvah rakrdan fakşi ńi daşdęį dańviġ maslah neńne ńu şu nemliţ. Dańviġ mişthi kaddaš da ve şu samslir kaċnah daċċęį miwwi katvlar şo mańfa şu raşwu. Nefgam şu samslir kaċnah miċke ċaiš daċgnin daċċęį kidgam daċsaķ kavta ve, dadah daglah, kavdiġ şu raşwu warċa vaċdhi kikvnin şu siknalar daċmlar ńu şu dańnęį tawfiš. Ş u daşwir aš daċvęį mişde ńu mińlah gaswdar mitńaš di daştdar daċċiġ daċċęį şed dadşi dalşdin. Vaċdiš, mişthi dańraš da faċşi ve şu siknal ċe deir raşdiš di manka fakllar nanrdar matńaķ di manka mańfa kifu şo şu daglaš ńi şu samslir raaķ:''')}


def save(key, text, receipt, group, changes):
    path = ROOT/'data/normalized'/f'{key}.json'
    if path.exists():
        raise ValueError(f'Preserve existing input: {key}')
    dump_json(path, normalized_document(key, receipt, text, kind='fl' if key.startswith('fl_') else 'source', group=group, transformations=changes))


def main():
    ledger = []
    for group, (url, original) in FL.items():
        repairs = {'Ş u': 'Şu', 'M aksu': 'Maksu'} if group == 'accidental_altruist' else {}
        text = original
        for old, new in repairs.items():
            text = text.replace(old, new)
        selected = []
        for atom in sentences(text):
            if len(' '.join(selected+[atom.text]).split()) > 180:
                break
            selected.append(atom.text)
        text = ' '.join(selected)
        receipt = snapshot(ROOT/'data/raw', url, content=original.encode(), acquisition_kind='indexed_web_excerpt',
                           locator='Indexed FL page inspected 2026-09-30; opening Kamri block before first embedded English paragraph; no raw/current HTTP claim')
        save('fl_'+group+'_v5', text, receipt, group,
             ['Complete opening sentences; 180 whitespace-word cap', f'Declared drop-cap joins: {repairs}'])
        ledger.append({'group': group, 'fl_status': 'indexed_excerpt', 'fl_words': len(text.split()),
                       'fl_sentences': len(selected), 'fl_url': url})
    receipt = json.loads((ROOT/'data/v5/capra_preview_exact.receipt.json').read_text())
    assert Path(receipt['artifact']).read_bytes().startswith(b'%PDF')
    pages = json.loads((ROOT/'data/v5/capra.pages.json').read_text())
    parts = []
    for page in pages[5:9]:
        page = re.sub(r'(?m)^\s*(?:[ivx]+\s+)?Foreword(?:\s+[ivx]+)?\s*$', '', page)
        page = re.sub(r'(?m)^\s*(?:[ivx]+|FRITJOF CAPRA)\s*$', '', page)
        parts.append(page)
    text = '\n'.join(parts)
    text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace('will playa crucial role', 'will play a crucial role')
    assert len(text.split()) <= 2000
    save('source_capra_foreword_v5', text, receipt, 'capra_foreword',
         ['pypdf extraction; publisher front matter PDF pages 6–9, printed ix–xii; whole Capra foreword',
          'Remove page/header labels and closing author name; join line-wrap hyphens; collapse whitespace',
          'Visual check PDF page 7 (printed x): repair will playa crucial role -> will play a crucial role'])
    shutil.copyfile(receipt['artifact'], ROOT/'data/v5/capra_frontmatter.pdf')
    ledger[0].update(source_status='available', source_id='source_capra_foreword_v5', source_words=len(text.split()),
                     source_url=receipt['requested_url'], qa='data/v5/qa/capra_page7.png')
    ledger[1].update(source_status='unavailable', source_id='source_accidental_altruist_v5',
        reason='Publisher chapter and PDF route return subscription HTML plus abstract, not chapter prose; no public author/institution chapter copy found in finite discovery.',
        source_url='https://link.springer.com/chapter/10.1007/978-3-642-37750-1_9', reference_edges=None)
    dump_json(ROOT/'benchmarks/inputs/register_v5_acquisition.json', ledger)
    old = json.loads((ROOT/'benchmarks/kamri_passage_v3a.json').read_text())
    record = next(r for r in old['records'] if r['group'] == 'models_magic')
    f = json.loads((ROOT/old['documents'][record['fl_id']]['path']).read_text())
    s = json.loads((ROOT/old['documents'][record['source_id']]['path']).read_text())
    audit = audit_aliases(f['text'], s['text'], record['edges'])
    dump_json(ROOT/'benchmarks/inputs/register_v5_alias_audit.json', {
        'group': 'models_magic', 'proposal_source': 'https://www.reddit.com/r/ForgottenLanguages/comments/1v1q1fw/i_translated_all_24_kamri_posts_on_forgotten/',
        'method': 'Existing reference-span presence and equal-length positional compatibility only; not independent semantic truth',
        'observations': audit, 'independent_source_works': 1, 'new_supported_lexical_entries': 0})
    print(json.dumps(ledger, indent=2))
    print('Alias evidence:', [(a['form'], a['state']) for a in audit])
    for key in ['fl_capra_foreword_v5', 'source_capra_foreword_v5']:
        document = json.loads((ROOT/'data/normalized'/f'{key}.json').read_text())
        for i, atom in enumerate(sentences(document['text'])):
            if key.startswith('fl_') or 'modern physics' in atom.text or 'consciousness' in atom.text:
                print(key, i, len(atom.tokens), atom.text)


if __name__ == '__main__':
    main()
