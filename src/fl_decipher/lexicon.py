"""Conservative positional baseline; entries are hypotheses with evidence links."""
from __future__ import annotations

from collections import Counter, defaultdict

from .text import Sentence


def induce(pairs: list[tuple[str, str, Sentence, Sentence]]) -> dict:
    counts = defaultdict(Counter)
    evidence = defaultdict(lambda: defaultdict(list))
    for pair_id, group, fl, en in pairs:
        if len(fl.tokens) != len(en.tokens):
            continue
        for f, e in zip(fl.tokens, en.tokens):
            counts[f.normalized][e.normalized] += 1
            evidence[f.normalized][e.normalized].append({"pair_id": pair_id, "source_group": group,
                                                        "fl_span": [f.start, f.end],
                                                        "source_span": [e.start, e.end]})
    result = {}
    for form in sorted(counts):
        total = sum(counts[form].values())
        candidates = []
        for meaning, count in sorted(counts[form].items(), key=lambda x: (-x[1], x[0])):
            support = evidence[form][meaning]
            candidates.append({"meaning": meaning, "count": count, "candidate_fraction": count / total,
                               "independent_groups": sorted({x["source_group"] for x in support}),
                               "evidence": support})
        result[form] = {"state": "proposed", "method": "equal_length_positional_v1",
                        "observations": total, "candidates": candidates,
                        "warning": "Candidate fractions are not calibrated probabilities; source order is assumed."}
    return result


def predict(sentence: Sentence, lexicon: dict, config: dict) -> list[dict]:
    result = []
    for token in sentence.tokens:
        entry = lexicon.get(token.normalized)
        best = entry["candidates"][0] if entry else None
        eligible = bool(best and best["count"] >= config["minimum_observations"]
                        and len(best["independent_groups"]) >= config["minimum_source_groups"]
                        and best["candidate_fraction"] >= config["minimum_candidate_fraction"])
        result.append({"surface": token.surface, "form": token.normalized, "span": [token.start, token.end],
                       "prediction": best["meaning"] if eligible else None,
                       "candidate": best["meaning"] if best else None,
                       "state": "supported_positional_candidate" if eligible else "abstained"})
    return result
