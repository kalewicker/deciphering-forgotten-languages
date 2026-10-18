"""Fixed-query accounting around the unchanged v38 literal matcher."""
import re
from fl_decipher.dated_capture_scope_v38 import literal_hits, normalized, quote_spans


def frozen_queries(target, previous):
    queries = quote_spans(target)
    assert len(queries) == 8
    assert queries == [{k: row[k] for k in ('quote_id', 'span', 'text', 'language_or_meaning_admitted')}
                       for row in previous['quotes']]
    return queries


def assess_queries(queries, pages, anchors, available):
    rows = []
    for q in queries:
        page_rows, hits = [], []
        for p in pages if available else []:
            found = literal_hits(q['text'], p['text']) if p['text'].strip() else None
            page_rows.append({'page': p['page'], 'text_available': bool(p['text'].strip()),
                              'literal_presence': bool(found) if found is not None else None,
                              'hits': found})
            hits += [{'page': p['page'], **h} for h in found or []]
        complete = available and bool(pages) and all(p['text'].strip() for p in pages)
        present = True if hits else False if complete else None
        rows.append({**q, 'source_hits': hits if available else None, 'page_results': page_rows,
                     'literal_source_presence': present})
    controls = []
    for p in pages if available else []:
        first = next((s for s in p['text'].splitlines() if s.strip()), None)
        hits = literal_hits(first, p['text']) if first is not None else None
        controls.append({'page': p['page'], 'query': first, 'own_page_hits': hits,
                         'passed': bool(hits) if hits is not None else None})
    marker = 'flv38literalabsencecontrol20261018'
    negative_hits = [{'page': p['page'], **h} for p in pages if p['text'].strip() for h in literal_hits(marker, p['text'])] if available else None
    complete = available and bool(pages) and all(p['text'].strip() for p in pages)
    def count(anchor, text):
        return len(re.findall(r'(?<!\w)'+re.escape(normalized(anchor))+r'(?!\w)', normalized(text)))
    anchor_rows = [{'anchor': a, 'source_page_counts': [{'page': p['page'], 'count': count(a, p['text']) if p['text'].strip() else None} for p in pages],
                    'source_observed_total': sum(count(a,p['text']) for p in pages), 'source_extraction_complete': complete}
                   for a in anchors] if available else None
    long = [r['literal_source_presence'] for r in rows if r['quote_id'] != 'quote01']
    primary = True if any(v is True for v in long) else None if any(v is None for v in long) else False
    return {'material_available': available, 'source_extraction_complete': complete, 'quote_denominator': 8,
            'source_page_denominator': len(pages), 'quotes': rows,
            'quotes_with_literal_source_presence': sum(r['literal_source_presence'] is True for r in rows) if available else None,
            'query_outcomes_unavailable': sum(r['literal_source_presence'] is None for r in rows),
            'long_quote_denominator': 7, 'long_quotes_with_literal_presence': sum(v is True for v in long) if available else None,
            'primary_long_block_presence': primary, 'expanded_name_literal_presence': rows[1]['literal_source_presence'],
            'positive_controls': controls, 'positive_controls_passed': sum(r['passed'] is True for r in controls) if available else None,
            'positive_controls_unavailable': sum(r['passed'] is None for r in controls),
            'negative_control': {'query': marker, 'source_hits': negative_hits,
                                 'passed': False if negative_hits else True if complete else None},
            'anchors': anchor_rows, 'semantic_evaluation_metrics': None, 'opaque_passages_scored': 0}
