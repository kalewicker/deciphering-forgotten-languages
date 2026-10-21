"""One fixed group-supported, unknown-neutral context predictor."""
from collections import Counter, defaultdict
from fl_decipher.word_order_v77 import fit as unigram_fit, UNK


def fit(grouped_sequences, vocab):
    allowed = set(vocab)
    prior = unigram_fit([s for _, s in grouped_sequences], vocab)[0]
    pairs = Counter()
    contexts = Counter()
    groups = defaultdict(set)
    for group, seq in grouped_sequences:
        for raw_a, raw_b in zip(seq, seq[1:]):
            if raw_a in allowed and raw_b in allowed:
                pairs[raw_a, raw_b] += 1
                contexts[raw_a] += 1
                groups[raw_a].add(group)
    eligible = {h for h, n in contexts.items() if n >= 5 and len(groups[h]) >= 2}
    return prior, pairs, contexts, groups, eligible


def predict(model, a, b):
    prior, pairs, contexts, groups, eligible = model
    if b == UNK or a not in eligible:
        return prior[b]
    mass = 1-prior[UNK]
    conditional = prior[b]/mass
    smoothed = (pairs[a,b]+10*conditional)/(contexts[a]+10)
    return mass*(.5*conditional+.5*smoothed)


def check_model(model):
    prior, _, _, _, eligible = model
    assert all(0 < x <= 1 for x in prior.values())
    from math import fsum, isclose
    assert isclose(fsum(prior.values()),1,abs_tol=1e-12)
    for h in eligible:
        values = [predict(model,h,w) for w in prior]
        assert all(0 < x <= 1 for x in values)
        assert isclose(fsum(values),1,abs_tol=1e-12)
        assert predict(model,h,UNK) == prior[UNK]
