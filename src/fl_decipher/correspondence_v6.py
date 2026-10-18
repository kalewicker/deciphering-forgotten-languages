"""Reference-guided diagnostics, never called by the retrieval scorer."""
from collections import Counter
from difflib import SequenceMatcher

from .alignment import similarity_features
from .passage_v3 import make_block
from .precision_v4 import block_reward, decode
from .register_v5 import ALIASES, audit_aliases, label_anchor_origins


def unit_count(ids, units):
    """Require complete consecutive protected units; partial groups are infeasible."""
    ids = tuple(ids)
    for start in range(len(units)):
        chosen = ()
        for stop in range(start, len(units)):
            chosen += tuple(units[stop])
            if chosen == ids:
                return stop-start+1
            if len(chosen) >= len(ids):
                break
    return None


def components(a, b, cfg, ps, fi):
    af, bf = a.features, b.features
    union = af['repetitions'] | bf['repetitions']
    values = {
        'length': min(af['length'], bf['length'])/max(af['length'], bf['length'], 1),
        'punctuation': SequenceMatcher(None, af['punctuation'], bf['punctuation'], autojunk=False).ratio(),
        'repetition': len(af['repetitions'] & bf['repetitions'])/len(union) if union else .5,
        'anchors': 1. if af['anchors'] & bf['anchors'] else .5,
    }
    structural = sum(cfg['weights'][k]*v for k, v in values.items())
    assert abs(structural-similarity_features(af, bf, cfg['weights'])) < 1e-12
    predicted = Counter(p['prediction'] for i in fi for p in ps[i] if p['prediction'] is not None)
    count = sum(predicted.values())
    overlap = sum(min(n, b.words[w]) for w, n in predicted.items())
    lexical = overlap/count if count else .5
    return {'feature_components': values, 'weighted_components': {k: cfg['weights'][k]*v for k, v in values.items()},
            'structural': structural, 'lexical': lexical, 'predictions': count, 'multiset_overlap': overlap,
            'prediction_capacity': [{'word': w, 'required': n, 'source_capacity': b.words[w],
                                     'unmatched': max(0, n-b.words[w]),
                                     'origins': dict(Counter(p['origin'] for i in fi for p in ps[i] if p['prediction'] == w))}
                                    for w, n in sorted(predicted.items())],
            'similarity': cfg['structural_weight']*structural + cfg['lexical_weight']*lexical,
            'fl_tokens': af['length'], 'source_tokens': bf['length'],
            'fl_punctuation': af['punctuation'], 'source_punctuation': bf['punctuation'],
            'shared_literal_anchors': sorted(af['anchors'] & bf['anchors'])}


def alias_capacity(fa, sa, reference):
    """Count contradictions to full one-to-one realization without selecting links."""
    result = []
    for i, f in enumerate(fa):
        ids = sorted({e['source_index'] for e in reference if e['fl_index'] == i})
        fw = Counter(t.normalized for t in f.tokens)
        sw = Counter(t.normalized for j in ids for t in sa[j].tokens)
        for form, proposal in ALIASES.items():
            if not fw[form]:
                continue
            result.append({'fl_index': i, 'form': form, 'proposal': proposal, 'fl_count': fw[form],
                           'source_count': sw[proposal], 'minimum_unrealized': max(0, fw[form]-sw[proposal]),
                           'compatible_fl_spans': [[t.start, t.end] for t in f.tokens if t.normalized == form],
                           'compatible_source_spans': [[t.start, t.end] for j in ids for t in sa[j].tokens if t.normalized == proposal],
                           'source_indices': ids, 'semantic_gold': False,
                           'status': 'insufficient_one_to_one_capacity' if fw[form] > sw[proposal] else 'capacity_only_not_confirmation'})
    return result


def audit(fa, sa, fl_text, source_text, reference, fu, su, ps, cfg):
    """Canonical reference blocks and adjacent unions are diagnostics only."""
    canonical = [(i,) for i in range(len(fa))]
    choices = canonical + [(i, i+1) for i in range(len(fa)-1)]
    rows = []
    for fi in choices:
        si = tuple(sorted({e['source_index'] for e in reference if e['fl_index'] in fi}))
        if not si:
            continue
        f, s = make_block(fa, fi), make_block(sa, si)
        fc, sc = unit_count(fi, fu), unit_count(si, su)
        feasible = fc is not None and sc is not None and fc <= 2 and sc <= 2
        values = components(f, s, cfg, ps, fi)
        reward = block_reward(values['similarity'], fc or 0, sc or 0, values['fl_tokens'], values['source_tokens'], cfg, 'tokens')
        block = {'fl_atoms': list(fi), 'source_atoms': list(si), 'fl_spans': list(f.spans),
                 'source_spans': list(s.spans), 'fl_effective_units': fc, 'source_effective_units': sc,
                 'similarity': values['similarity']}
        provisional = label_anchor_origins(decode({'blocks': [block]}, fa, sa, ps, cfg, 'ordered'), ps)
        rows.append({**block, **values, 'canonical': len(fi) == 1, 'proposal_feasible': feasible,
                     'reward': reward, 'positive_reward': reward > 0, 'eligible_reference_proposal': feasible and reward > 0,
                     'reference_guided_token_hypotheses': provisional['token_pairs'],
                     'token_hypotheses_used_by_retrieval': False, 'semantic_gold': False})
    atoms = []
    for row in rows:
        if not row['canonical']:
            continue
        i = row['fl_atoms'][0]
        atoms.append({'fl_index': i, 'fl_tokens': row['fl_tokens'], 'source_tokens': row['source_tokens'],
                      'token_count_delta': row['fl_tokens']-row['source_tokens'],
                      'fl_punctuation': row['fl_punctuation'], 'source_punctuation': row['source_punctuation'],
                      'fl_numeric_literals': sorted({t.surface for t in fa[i].tokens if t.surface.isnumeric()}),
                      'source_numeric_literals': sorted({t.surface for j in row['source_atoms'] for t in sa[j].tokens if t.surface.isnumeric()}),
                      'shared_literal_anchors': row['shared_literal_anchors'], 'semantic_gold': False})
    return {'reference_proposals': rows, 'atom_audit': atoms,
            'alias_observations': audit_aliases(fl_text, source_text, reference),
            'alias_capacity': alias_capacity(fa, sa, reference),
            'feasible_reference_proposals': sum(r['proposal_feasible'] for r in rows),
            'positive_feasible_reference_proposals': sum(r['eligible_reference_proposal'] for r in rows),
            'reference_atoms_in_positive_proposals': sorted({i for r in rows if r['eligible_reference_proposal'] for i in r['fl_atoms']}),
            'semantic_gold': False, 'diagnostic_only': True}
