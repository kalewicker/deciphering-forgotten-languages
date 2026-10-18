"""Acquisition contracts for a bounded natural holdout; no model evaluation."""
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess

from .corpus import digest, dump_json
from .text import sentences

NOMINATIONS = [
    {'id': 'liber_azazel', 'title': 'Liber Azazel', 'component': 'liber_azazel',
     'inventory_entry': 9, 'fl_url': 'https://forgottenlanguages-full.forgottenlanguages.org/2019/06/su-dacflar-ni-azazil.html',
     'source_scope': 'Book I, opening complete sentences up to 2000 whitespace words',
     'source_routes': [
         'https://www.scribd.com/doc/47586429/Liber-Azazel',
         'https://www.magicgatebg.com/Books/Aleister%20Crowley/Liber%20Azazel.pdf',
         'https://theisticsatanism.com/']},
    {'id': 'vile_darkness', 'title': 'Book of Vile Darkness', 'component': 'vile_exalted_component',
     'inventory_entry': 15, 'fl_url': 'https://forgottenlanguages-full.forgottenlanguages.org/2022/06/kargit-kiru.html',
     'source_scope': '2002 Monte Cook edition, chapter 1 opening complete sentences up to 2000 whitespace words',
     'source_routes': [
         'https://openlibrary.org/books/OL8144288M/Book_of_Vile_Darkness',
         'https://archive.org/metadata/bookviledarkness00cook']},
]


def utc():
    return datetime.now(timezone.utc).isoformat()


def opening(text, cap=180, numbered=False):
    """Select once by order/length; do not backfill over-budget statements."""
    clean = re.sub(r'(?m)^\s*\d+\.\s*', '', text) if numbered else text
    clean = re.sub(r'\s+', ' ', clean).strip()
    selected = []; pending = []
    for atom in sentences(clean):
        pending.append(atom.text)
        if not re.search(r'[.!?]$', atom.text):
            continue
        statement = ' '.join(pending); pending = []
        if len(' '.join(selected+[statement]).split()) > cap:
            break
        selected.append(statement)
    return ' '.join(selected)



def fetch(root, key, url):
    """One raw request, preserving error bodies/headers without printing them."""
    directory = root/key
    directory.mkdir(parents=True, exist_ok=False)
    body, headers = directory/'body.bin', directory/'headers.txt'
    began = utc()
    result = subprocess.run(['curl', '--silent', '--show-error', '--location', '--max-time', '30',
                            '--user-agent', 'FL-Decipher/0.1 finite research pilot',
                            '--output', str(body), '--dump-header', str(headers),
                            '--write-out', '%{url_effective}\n%{http_code}', url], capture_output=True)
    parts = result.stdout.decode(errors='replace').rsplit('\n', 1)
    status = int(parts[-1]) if len(parts)==2 and parts[-1].isdigit() else None
    receipt = {'requested_url': url, 'acquisition_kind': 'raw_http_attempt', 'started_at_utc': began,
               'finished_at_utc': utc(), 'final_url': parts[0] if len(parts)==2 else None,
               'http_status': status, 'curl_returncode': result.returncode,
               'error': result.stderr.decode(errors='replace') or None,
               'artifacts': {}}
    for path in (body, headers):
        if path.exists():
            receipt['artifacts'][path.name] = {'path': str(path.resolve()), 'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
    dump_json(directory/'receipt.json', receipt)
    return receipt


def reference_gate(*, source_prose, authority_verified, extraction_reviewed, passage_reviewed, component_novel):
    """Every evidence gate must pass; acquisition success alone is insufficient."""
    values = locals()
    assert all(type(v) is bool for v in values.values())
    return {'eligible': all(values.values()), 'requirements': values,
            'unmet': [k for k, v in values.items() if not v]}


def validate_denominators(ledger):
    assert [r['id'] for r in ledger['records']] == [r['id'] for r in NOMINATIONS]
    assert ledger['selected_works'] == ledger['selected_queries'] == 2
    assert ledger['selected_components'] == len({r['component'] for r in NOMINATIONS}) == 2
    assert ledger['reference_eligible_queries'] == sum(r['gate']['eligible'] for r in ledger['records'])
    if not ledger['reference_eligible_queries']:
        assert ledger['evaluated_queries'] == 0 and ledger['metrics'] is None and not ledger['model_executed']
    for row, nomination in zip(ledger['records'], NOMINATIONS, strict=True):
        assert row['component'] == nomination['component'] and row['fl_url'] == nomination['fl_url']
        assert row['gate'] == reference_gate(**row['gate']['requirements'])
        if not row['gate']['eligible']:
            assert row['references'] is None and row['lexical_accuracy'] is None
    return True
