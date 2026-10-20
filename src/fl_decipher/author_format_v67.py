"""Explicit two-form author grammar layered over the unchanged E66 evidence."""
import re
from fl_decipher.arxiv_feasibility_v66 import norm, metadata as legacy_metadata, first_page_checks as legacy_page_checks

TOKEN = re.compile(r"(?:[a-z]+(?:[-'][a-z]+)*|[a-z]\.)")
REJECT = {'and', 'jr', 'sr', 'ii', 'iii', 'iv'}


def parse_author(literal):
    if not isinstance(literal, str):
        return None
    text = norm(literal)
    if any(c in text for c in ';&/0123456789') or text.count(',') > 1:
        return None
    if ',' in text:
        family, given = (v.strip() for v in text.split(','))
        family_words, given_words = family.split(), given.split()
        form = 'family_comma_given'
    else:
        words = text.split()
        family_words, given_words = words[-1:], words[:-1]
        form = 'given_family'
    tokens = family_words + given_words
    if len(family_words) != 1 or not given_words or any(not TOKEN.fullmatch(t) or t.rstrip('.') in REJECT for t in tokens):
        return None
    # A family name is not a one-letter abbreviation.
    if len(family_words[0].rstrip('.')) < 2 or family_words[0].endswith('.'):
        return None
    return {'family': family_words[0], 'given': [t.rstrip('.') for t in given_words], 'form': form}


def assess_metadata(raw, receipt, cfg, frozen_assessment):
    old = legacy_metadata(raw, receipt, cfg)
    if old != frozen_assessment:
        raise ValueError('E66 metadata replay differs from frozen result')
    authors = old['native_authors']
    name = parse_author(authors[0]) if len(authors) == 1 else None
    compatible = bool(name and name['family'] == cfg['author_family'] and name['given'][0].startswith(cfg['author_initial']))
    checks = {k: v for k, v in old['checks'].items() if k != 'single_compatible_author'}
    checks['single_unambiguous_compatible_author'] = compatible
    return {'e66_metadata_replay': old, 'parsed_author': name, 'native_author_literal': authors[0] if len(authors) == 1 else None,
            'checks': checks, 'passed': all(checks.values()), 'unmet': [k for k, v in checks.items() if not v],
            'correction_after_observed_failure': True, 'citation_version_unspecified': True,
            'actual_fl_source_edition_established': False}


def author_witnesses(text, name):
    if not name:
        return []
    hay = norm(text)
    # All metadata given components are retained. A one-letter component may
    # display its initial period; no full-name/initial substitution is allowed.
    given = r'\s+'.join(re.escape(t) + (r'\.?' if len(t) == 1 else '') for t in name['given'])
    family = re.escape(name['family'])
    forms = [('given_family', given + r'\s+' + family), ('family_comma_given', family + r'\s*,\s*' + given)]
    found = []
    for form, pattern in forms:
        for m in re.finditer(r'(?<!\w)' + pattern + r'(?!\w)', hay):
            found.append({'form': form, 'normalized_span': list(m.span()), 'normalized_witness': m.group()})
    return sorted(found, key=lambda x: (x['normalized_span'], x['form']))


def assess_first_page(text, pages, other_pages, receipt, cfg, name):
    old = legacy_page_checks(text, pages, other_pages, receipt, cfg, [])
    checks = {k: v for k, v in old['checks'].items() if k != 'metadata_author_in_first_page'}
    hits = author_witnesses(text, name)
    checks['parsed_complete_metadata_name_in_first_page'] = bool(hits)
    return {'checks': checks, 'passed': all(checks.values()), 'unmet': [k for k, v in checks.items() if not v],
            'author_witnesses': hits, 'witness_coordinate_system': 'NFC_casefold_whitespace_normalized_first_page'}
