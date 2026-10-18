"""Structural local alignment. No lexicon, bibliography, or source answers used."""
from __future__ import annotations

from difflib import SequenceMatcher
import re

from .text import Sentence


def features(sentence: Sentence) -> dict:
    words = [t.normalized for t in sentence.tokens]
    repetitions = {(i, j) for j, w in enumerate(words) for i in range(j) if words[i] == w}
    return {"length": len(words), "punctuation": "".join(re.findall(r"[,;:()?!]", sentence.text)),
            "repetitions": repetitions,
            "anchors": {w for w in words if w.isnumeric() or (w.isascii() and len(w) > 2)}}


def similarity_features(a: dict, b: dict, weights: dict) -> float:
    length = min(a["length"], b["length"]) / max(a["length"], b["length"], 1)
    punctuation = SequenceMatcher(None, a["punctuation"], b["punctuation"], autojunk=False).ratio()
    union = a["repetitions"] | b["repetitions"]
    repetition = len(a["repetitions"] & b["repetitions"]) / len(union) if union else 0.5
    # Only literal ASCII strings/numerals; absent shared anchors provide no confirmation.
    anchor = 1.0 if a["anchors"] & b["anchors"] else 0.5
    values = {"length": length, "punctuation": punctuation, "repetition": repetition, "anchors": anchor}
    return sum(weights[k] * values[k] for k in weights)


def local_align(fl: list[Sentence], source: list[Sentence], config: dict) -> dict:
    """Smith-Waterman baseline with 1:1 links and explicit gaps; lengths are bounded by input."""
    n, m = len(fl), len(source)
    if not n or not m:
        return {"strength": 0.0, "links": [], "gaps": [], "fl_sentences": n}
    af, bf = list(map(features, fl)), list(map(features, source))
    scores = [[0.0] * (m + 1) for _ in range(n + 1)]
    trace = [[0] * (m + 1) for _ in range(n + 1)]
    similarities = [[0.0] * m for _ in range(n)]
    best = (0.0, 0, 0)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = similarity_features(af[i - 1], bf[j - 1], config["weights"])
            similarities[i - 1][j - 1] = sim
            # Disallow a negative diagonal masquerading as a supported sentence link.
            diagonal = scores[i - 1][j - 1] + sim - config["match_floor"] if sim > config["match_floor"] else -1
            choices = [0.0, diagonal, scores[i - 1][j] - config["gap_penalty"],
                       scores[i][j - 1] - config["gap_penalty"]]
            move = max(range(4), key=lambda k: choices[k])
            scores[i][j], trace[i][j] = choices[move], move
            if choices[move] > best[0]:
                best = (choices[move], i, j)
    value, i, j = best
    links, gaps = [], []
    while i and j and scores[i][j] > 0:
        move = trace[i][j]
        if move == 1:
            links.append({"fl_index": i - 1, "source_index": j - 1,
                          "similarity": similarities[i - 1][j - 1]})
            i, j = i - 1, j - 1
        elif move == 2:
            gaps.append({"side": "fl", "index": i - 1})
            i -= 1
        elif move == 3:
            gaps.append({"side": "source", "index": j - 1})
            j -= 1
        else:
            break
    return {"strength": value / max(n, 1), "links": list(reversed(links)),
            "gaps": list(reversed(gaps)), "fl_sentences": n,
            "minimum_links_met": len(links) >= config["minimum_links"]}


def rank_sources(fl: list[Sentence], candidates: dict[str, list[Sentence]], config: dict) -> list[dict]:
    ranked = [{"source_id": key, **local_align(fl, source, config)} for key, source in candidates.items()]
    return sorted(ranked, key=lambda x: (-x["strength"], x["source_id"]))
