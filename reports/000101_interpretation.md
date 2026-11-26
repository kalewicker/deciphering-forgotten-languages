# E101 finds pairing specificity within the exposed Burton post

The registered token rule ranked the package-assigned English above the
same-excerpt alternative on **21 of 22 held-out queries**. It scored every query.
Its all-query score was **95.5%**, compared with **75.0%** for the length baseline
and **59.1%** for the median of 999 shuffled-training replicates. Each of the six
registered development criteria passed. This supports a separate replication on
reserved source material.

| Excerpt | Queries | Token wins / ties / losses / abstentions | Length wins / ties / losses / abstentions |
|---|---:|---:|---:|
| Pages 254–256 | 18 | 17 / 0 / 1 / 0 | 8 / 9 / 1 / 0 |
| Pages 252–253 | 4 | 4 / 0 / 0 / 0 | 4 / 0 / 0 / 0 |
| Overall | 22 | 21 / 0 / 1 / 0 | 12 / 9 / 1 / 0 |

Wins earn one point, ties and abstentions earn half a point, and losses earn
zero. The token rule's advantage over length was 20.5 percentage points, all
from the longer excerpt. The four-row excerpt reached the same ceiling under
both rules. The one token loss was package ordinal 19. The shuffle's overall
95th percentile was 16/22 points, or 72.7%. Zero of 999 replicates reached the
observed overall score. Within the four-row excerpt alone, 119 replicates
reached the observed score. Overlapping folds make this a descriptive reference
distribution.

Each fold held out its query and distractor on both sides, leaving 20 training
pairs. The distractor was the closest by English token count within the excerpt,
using the assigned answer's length to construct the comparison. The scorer used
text features without row or page order. The fold mask suppressed identical token
forms present on both sides, including names when spelled the same. Repeated
names in different scripts, topic vocabulary and other shared content could
still contribute. Each query had a single length-matched alternative, so the
result measures the registered two-choice task. Both excerpts come from one
exposed work, and folds may train across excerpts. [Registered protocol](../experiments/burton_pairing_v101.md)

The finding links the Yid text to the package's proposed pairing labels within
this work. Generalization to another work and semantic accuracy remain open.
Independent semantic benchmark capacity stays at 0/4. The result warrants
testing the frozen rule on a separately reserved source group with the same
controls. This run admits zero untouched units.

The first verification script introduced floating-point arithmetic when a
training row had zero query-token overlap and failed an exact score assertion.
The original verifier and failure receipt are preserved. A new verifier
initializes the sum with exact rational zero. It independently reproduced the
fold assignments, observed and length scores, all 21,978 shuffled fold scores
and all six decision checks against the sealed output. The original scoring
run stands. All 692 workspace tests and 653 isolated public tests passed.
[Verification receipt](000101_verification.json)

Replay the verification with the local archive using
`.venv/bin/python scripts/verify_burton_pairing_v101_r2.py`. The tokenized fold
plan, individual scores and verification failure receipt stay in local evidence.
