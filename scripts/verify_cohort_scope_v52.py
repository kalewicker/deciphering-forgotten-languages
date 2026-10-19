"""Reconstruct static channel spans/runs with independent traversal and accounting."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from bs4 import BeautifulSoup
from bs4.element import CData, NavigableString, Tag
from fl_decipher.heading_scope_v51 import audit as frozen_title_audit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_publisher_intake_v50 import key


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def digest(s): return hashlib.sha256(s.encode()).hexdigest()


def reconstruct(raw, frozen_body, selector):
    soup = BeautifulSoup(raw, 'html.parser')
    tags = [n for n in soup.descendants if isinstance(n, Tag)]; ordinals = {id(t): i for i, t in enumerate(tags)}
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    bodies = soup.select('body'); containers = soup.select(selector); assert len(bodies) == len(containers) == 1
    body = bodies[0]; container = containers[0]; assert body.get_text(' ', strip=True) == frozen_body
    nodes = [s for s in body.strings if type(s) in (NavigableString, CData) and str(s).strip()]
    body_rows = []; positions = {}; lengths = []
    for i, node in enumerate(nodes):
        text = str(node).strip(); at = sum(lengths) + i
        row = {'body_leaf_index': i, 'parent_dom_index': ordinals[id(node.parent)], 'text': str(node),
               'stripped_text': text, 'body_span': [at, at + len(text)]}
        positions[id(node)] = row; body_rows.append(row); lengths.append(len(text))
        assert frozen_body[at:at + len(text)] == text
    assert ' '.join(r['stripped_text'] for r in body_rows) == frozen_body
    categories = [('form', ['form', 'button', 'input', 'label']), ('table', ['table', 'thead', 'tbody', 'tr', 'td', 'th']),
                  ('figure', ['figure', 'figcaption']), ('blockquote', ['blockquote']), ('list', ['ul', 'ol', 'li']),
                  ('heading', ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']), ('paragraph', ['p'])]
    rows = []
    for child in container.children:
        strings = child.strings if isinstance(child, Tag) else [child]
        for node in strings:
            if id(node) not in positions: continue
            parents = []
            for p in node.parents:
                if p is container: break
                parents.append(p)
            channel = 'other'; owner = child if isinstance(child, Tag) else container
            for name, names in categories:
                matches = [p for p in parents if p.name in names]
                if matches: channel = name; owner = matches[-1]; break
            rows.append({'leaf_index': len(rows), **positions[id(node)], 'parent_tag': node.parent.name,
                'ancestor_tags_to_container': [p.name for p in parents], 'direct_child_tag': child.name if isinstance(child, Tag) else None,
                'old_direct_p_included': isinstance(child, Tag) and child.name == 'p', 'channel': channel,
                'owner_dom_index': ordinals[id(owner)], 'owner_tag': owner.name})
    paragraphs = []
    for p in container.select('p'):
        strings = [s for s in p.strings if id(s) in positions]; text = p.get_text(' ', strip=True)
        span = [positions[id(strings[0])]['body_span'][0], positions[id(strings[-1])]['body_span'][1]] if strings else None
        paragraphs.append({'paragraph_index': len(paragraphs), 'dom_index': ordinals[id(p)], 'direct_child': p.parent is container,
            'text': text, 'body_span': span, 'body_span_text_matches': frozen_body[slice(*span)] == text if span else text == '',
            'descendant_body_leaf_indices': [positions[id(s)]['body_leaf_index'] for s in strings], 'nested_p_descendants': len(p.select('p'))})
    legacy = []
    for child in container.children:
        if not isinstance(child, Tag) or child.name != 'p': continue
        text = child.get_text(' ', strip=True); count = frozen_body.count(text) if text else 0
        at = frozen_body.find(text) if count == 1 else None
        legacy.append({'unit': len(legacy), 'text': text, 'span': [at, at + len(text)] if at is not None else None, 'body_mapping_count': count})
    groups = []; current = []
    for row in rows + [None]:
        same = (row is not None and row['channel'] == 'paragraph' and current
                and row['owner_dom_index'] == current[-1]['owner_dom_index']
                and row['leaf_index'] == current[-1]['leaf_index'] + 1
                and row['body_span'][0] == current[-1]['body_span'][1] + 1)
        if current and not same: groups.append(current); current = []
        if row is not None and row['channel'] == 'paragraph': current.append(row)
    runs = []
    for group in groups:
        span = [group[0]['body_span'][0], group[-1]['body_span'][1]]
        runs.append({'unit': len(runs), 'owner_dom_index': group[0]['owner_dom_index'], 'body_span': span,
                     'leaf_indices': [r['leaf_index'] for r in group], 'text': frozen_body[slice(*span)]})
    full = container.get_text(' ', strip=True); direct = ' '.join(p['text'] for p in legacy if p['text'])
    assert ' '.join(r['stripped_text'] for r in rows) == full
    assert ' '.join(r['stripped_text'] for r in rows if r['old_direct_p_included']) == direct
    counts = dict(sorted(Counter(r['channel'] for r in rows).items()))
    scope = {'body_text_sha256': digest(frozen_body), 'body_text': frozen_body, 'body_leaves': body_rows,
        'container_text': full, 'container_text_sha256': digest(full), 'legacy_direct_paragraphs': legacy,
        'legacy_direct_p_text': direct, 'legacy_direct_p_text_sha256': digest(direct), 'container_leaves': rows,
        'paragraph_inventory': paragraphs, 'paragraph_runs': runs, 'channel_leaf_counts': counts,
        'channel_characters': {c: sum(len(r['stripped_text']) for r in rows if r['channel'] == c) for c in counts},
        'added_paragraph_leaf_indices': [r['leaf_index'] for r in rows if r['channel'] == 'paragraph' and not r['old_direct_p_included']],
        'removed_legacy_leaf_indices': [r['leaf_index'] for r in rows if r['channel'] != 'paragraph' and r['old_direct_p_included']]}
    covered = [i for r in runs for i in r['leaf_indices']]; selected = [r['leaf_index'] for r in rows if r['channel'] == 'paragraph']
    checks = {'every_body_leaf_span_exact': all(frozen_body[slice(*r['body_span'])] == r['stripped_text'] for r in body_rows),
        'every_container_leaf_span_exact': all(frozen_body[slice(*r['body_span'])] == r['stripped_text'] for r in rows),
        'paragraph_inventory_spans_exact': all(r['body_span_text_matches'] for r in paragraphs),
        'paragraph_runs_cover_selected_leaves_once': covered == selected and len(covered) == len(set(covered)),
        'run_spans_ordered_disjoint': all(a['body_span'][1] <= b['body_span'][0] for a, b in zip(runs, runs[1:])),
        'every_run_matches_original_span': all(frozen_body[slice(*r['body_span'])] == r['text'] == ' '.join(rows[i]['stripped_text'] for i in r['leaf_indices']) for r in runs),
        'all_channel_leaves_accounted': sum(counts.values()) == len(rows),
        'all_channel_characters_accounted': sum(scope['channel_characters'].values()) == sum(len(r['stripped_text']) for r in rows),
        'no_form_leaf_in_paragraph_runs': all(rows[i]['channel'] != 'form' for i in covered)}
    return scope, checks


def main():
    run = ROOT / 'runs/000052_cohort_scope'; check_hashes(run)
    cfg = read('experiments/cohort_scope_v52.json'); pre = read('data/v52/preflight.json')
    manifest = read('runs/000052_cohort_scope/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/cohort_scope_v52.json'] == sha('experiments/cohort_scope_v52.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc'] and cfg['request_budget'] == 0
    assert cfg['page_denominator'] == len(cfg['pages']) == 5
    assert [p['id'] for p in cfg['pages']] == ['reference_v42', 'q00s00', 'q00s01', 'q01s00', 'q01s01']
    intake = read('runs/000050_publisher_intake/report.json'); assert intake['ready_captures'] == 1 and intake['intake_capacity_met'] is False
    summaries = []; total_leaves = 0
    for spec in cfg['pages']:
        raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt']); original = read(spec['observation'])
        assert receipt['artifacts']['body.bin']['sha256'] == sha(spec['raw']) and receipt['transport_complete']
        body = original[spec['body_field']]; scope, checks = reconstruct(raw, body, cfg['selector'])
        assert read(f"data/v52/{spec['id']}_scope.json") == scope
        # Title diagnostics deliberately replay the sealed v51 helper; critical URL fields are checked separately.
        identity = frozen_title_audit(raw, spec['expected_title'], spec['url'], receipt['final_url'], cfg['selector'])
        assert read(f"data/v52/{spec['id']}_title_identity.json") == identity
        assert identity['body_text'] == body and identity['paragraph_units'] == scope['legacy_direct_paragraphs']
        soup = BeautifulSoup(raw, 'html.parser')
        urls = [('canonical', t.get('href', '')) for t in soup.select('link[rel=canonical]')]
        urls += [('og_url', t.get('content', '')) for t in soup.select('meta[property="og:url"]')]
        assert identity['identity_inventory'] == [{'channel': c, 'value': u, 'matches_nominee': key(u) == key(spec['url']) and key(spec['url']) is not None} for c, u in urls]
        agrees = all(key(u) == key(spec['url']) for _, u in urls) and {'canonical', 'og_url'} <= {c for c, _ in urls} and key(receipt['final_url']) == key(spec['url'])
        assert identity['identity_urls_agree'] == agrees
        if spec['id'] == 'reference_v42':
            assert [{k: r[k] for k in ['unit', 'span', 'text']} for r in scope['legacy_direct_paragraphs']] == read('data/v46/scope.json')['source_units']
            ready = None
        else:
            assert scope['legacy_direct_paragraphs'] == original['paragraph_units']
            ready = next(r['ready_for_future_registration'] for r in intake['slot_results'] if r['slot_id'] == spec['id'])
            assert ready == original['ready_for_future_registration']
        if spec['id'] == 'q01s01': assert identity == read('data/v51/audit.json')
        leaves = scope['container_leaves']; ps = scope['paragraph_inventory']; total_leaves += len(leaves)
        summaries.append({'id': spec['id'], 'title': spec['expected_title'], 'url': spec['url'],
            'legacy_direct_paragraphs': len(scope['legacy_direct_paragraphs']), 'paragraph_owner_inventory': len(ps),
            'empty_paragraph_owners': sum(not p['text'] for p in ps), 'owners_with_nested_p': sum(p['nested_p_descendants'] > 0 for p in ps),
            'container_leaf_count': len(leaves), 'legacy_included_leaf_count': sum(r['old_direct_p_included'] for r in leaves),
            'paragraph_channel_leaf_count': scope['channel_leaf_counts'].get('paragraph', 0), 'paragraph_runs': len(scope['paragraph_runs']),
            'added_paragraph_leaf_count': len(scope['added_paragraph_leaf_indices']), 'removed_legacy_leaf_count': len(scope['removed_legacy_leaf_indices']),
            'channel_leaf_counts': scope['channel_leaf_counts'], 'channel_characters': scope['channel_characters'],
            'legacy_direct_p_characters': len(scope['legacy_direct_p_text']), 'prospective_paragraph_run_characters': sum(len(r['text']) for r in scope['paragraph_runs']),
            'all_document_h1_count': identity['all_document_h1_count'], 'descriptive_metadata_agreement': identity['descriptive_metadata_agreement'],
            'identity_urls_agree': agrees, 'v50_ready_unchanged': ready, 'old_scope_reproduced': True,
            'accounting_checks': checks, 'accounting_passed': all(checks.values())})
    report = read('runs/000052_cohort_scope/report.json'); gate = all(r['accounting_passed'] for r in summaries)
    assert report['pages'] == summaries and report['page_denominator'] == 5
    assert report['registered_engineering_accounting_gate'] == gate and report['outcome'] == ('uniform_accounting_verified' if gate else 'accounting_failure')
    assert report['pages_with_added_paragraph_leaves'] == sum(r['added_paragraph_leaf_count'] > 0 for r in summaries)
    assert report['pages_with_removed_legacy_leaves'] == sum(r['removed_legacy_leaf_count'] > 0 for r in summaries)
    assert report['v50_ready_captures_unchanged'] == 1 and report['v50_intake_capacity_met_unchanged'] is False
    for k in ['network_requests', 'browser_renders', 'new_structural_scores', 'opaque_lexical_or_semantic_scores',
              'new_candidate_readiness_admissions', 'semantic_labels_admitted', 'source_identities_admitted', 'independent_reviews_admitted',
              'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 51
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000052_cohort_scope/manifest.json'), 'all_five_pages_reconstructed': True,
        'container_text_leaves_verified': total_leaves, 'body_spans_channels_owners_and_runs_reconstructed': True,
        'old_bodies_scopes_and_readiness_preserved': True, 'title_diagnostics_replay_shared_sealed_v51_helper': True,
        'critical_identity_urls_checked_separately': True, 'shared_html_parser': 'BeautifulSoup html.parser',
        'browser_visibility_or_semantic_scope_validated': False, 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    out = ROOT / 'reports/000052_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(prior), 'container_leaves': total_leaves, 'accounting_gate': gate}, indent=2))


if __name__ == '__main__': main()
