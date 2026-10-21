"""Fixed next-category prediction, with no fitting on evaluation groups."""
from collections import Counter
from hashlib import sha256
from math import log2, fsum

UNK = '<UNK>'


def segments(row):
    out = []
    for i, t in enumerate(row['tokens']):
        if t['blocked']:
            continue
        if not t['pair_from_previous']:
            out.append([])
        out[-1].append(i)
    return out


def order(draw, uid, segment):
    return sorted(segment, key=lambda i: (sha256(f'v77|{draw}|{uid}|{segment[0]}|{i}'.encode()).digest(), i))


def vocabulary(sequences):
    counts = Counter(w for seq in sequences for w in seq)
    return sorted(w for w, n in counts.items() if n >= 2)


def fit(sequences, vocab):
    allowed = set(vocab)
    seqs = [[w if w in allowed else UNK for w in seq] for seq in sequences]
    words = Counter(w for seq in seqs for w in seq)
    pairs = Counter((a,b) for seq in seqs for a,b in zip(seq,seq[1:]))
    contexts = Counter()
    for (a,b), n in pairs.items():
        contexts[a] += n
    total = sum(words.values())
    prior = {w:(words[w]+0.5)/(total+0.5*(len(vocab)+1)) for w in [*vocab,UNK]}
    return prior, pairs, contexts


def predict(model, a, b):
    prior, pairs, contexts = model
    return (pairs[a,b]+10*prior[b])/(contexts[a]+10)


def mean(xs):
    return fsum(xs)/len(xs) if xs else None


def metrics(u, p, known):
    ul = [-log2(x) for x in u]; pl = [-log2(x) for x in p]
    gains = [a-b for a,b in zip(ul,pl,strict=True)]
    return {'unigram_loss':mean(ul),'context_loss':mean(pl),'gain':mean(gains),
            'known_targets':sum(known),
            'known_unigram_loss':mean([x for x,k in zip(ul,known) if k]),
            'known_context_loss':mean([x for x,k in zip(pl,known) if k]),
            'known_gain':mean([x for x,k in zip(gains,known) if k])}


def summarize(folds):
    gains = [f['observed']['gain'] for f in folds]
    known = [f['observed']['known_gain'] for f in folds]
    observed = mean(gains)
    controls = [mean([f['controls'][d]['gain'] for f in folds]) for d in range(99)]
    rank = (1+sum(x >= observed for x in controls))/100
    kg = mean(known) if all(x is not None for x in known) else None
    components = {'macro_gain_at_least_005': observed >= .05,
                  'positive_at_least_10_groups':sum(x>0 for x in gains)>=10,
                  'known_targets_at_least_20_each':all(f['observed']['known_targets']>=20 for f in folds),
                  'known_macro_gain_positive':kg is not None and kg>0,
                  'conditional_rank_at_most_005':rank<=.05}
    return {'groups':len(folds),'pairs':sum(f['pairs'] for f in folds),
            'macro_gain':observed,'macro_known_gain':kg,'positive_groups':sum(x>0 for x in gains),
            'token_weighted_gain':fsum(f['pairs']*f['observed']['gain'] for f in folds)/sum(f['pairs'] for f in folds),
            'control_macro_gains':controls,'conditional_rank':rank,
            'gate_components':components,'development_gate':all(components.values())}
