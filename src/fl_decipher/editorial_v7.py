"""Three fixed scoring ablations; identity labels never enter this module."""
from array import array
from collections import Counter
from difflib import SequenceMatcher

from .alignment import similarity_features
from .passage_v3 import ScoreCache

VARIANTS = [{'id': f'p{p}_r{r}_l{l}', 'punctuation_neutral': bool(p),
             'relative_repetition': bool(r), 'lexical_neutral': bool(l)}
            for p in range(2) for r in range(2) for l in range(2)]


def relative_pairs(features, bins=8):
    n = max(features['length'], 1)
    return Counter((bins*i//n, bins*j//n) for i, j in features['repetitions'])


def multiset_jaccard(a, b):
    union = sum((a | b).values())
    return sum((a & b).values())/union if union else .5


class EditorialScoreCache(ScoreCache):
    def __init__(self, fl_atoms, source, cfg, predictions, variant):
        super().__init__(fl_atoms, source, cfg, predictions)
        self.variant = variant
        self.editorial_rows = {}

    def row(self, ids, source_size, scoring):
        if self.variant['id'] == 'p0_r0_l0':
            return super().row(ids, source_size, scoring)
        key = (ids, source_size, scoring)
        if key not in self.editorial_rows:
            f = self.block(ids)
            predicted = Counter(p['prediction'] for i in ids for p in self.predictions[i] if p['prediction'] is not None)
            count = sum(predicted.values())
            values = array('d')
            for target in self.source.blocks[source_size]:
                af, bf = f.features, target.features
                structural = similarity_features(af, bf, self.cfg['weights'])
                if self.variant['punctuation_neutral']:
                    original = SequenceMatcher(None, af['punctuation'], bf['punctuation'], autojunk=False).ratio()
                    structural += self.cfg['weights']['punctuation']*(.5-original)
                if self.variant['relative_repetition']:
                    union = af['repetitions'] | bf['repetitions']
                    original = len(af['repetitions'] & bf['repetitions'])/len(union) if union else .5
                    relative = multiset_jaccard(relative_pairs(af), relative_pairs(bf))
                    structural += self.cfg['weights']['repetition']*(relative-original)
                matched = sum(min(n, target.words[w]) for w, n in predicted.items())
                lexical = matched/count if count else .5
                if count and self.variant['lexical_neutral']:
                    lexical = .5+.5*lexical
                values.append(structural if scoring == 'structural' else self.cfg['structural_weight']*structural+self.cfg['lexical_weight']*lexical)
            self.editorial_rows[key] = values
        return self.editorial_rows[key]
