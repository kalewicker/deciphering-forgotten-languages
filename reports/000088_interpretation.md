# E88: little longer exact repetition in the saved development gains

E79’s positive gains coincide mainly with previously observed **two-token pairs**,
with little contribution from longer exact sequences. Of 1,918 targets, 16 lie
inside matching three-token windows and six inside matching four-token windows.
No five- through eight-token windows match across the fixed fold boundary.
Three-token coverage accounts for **6.41% of positive gain mass**; four-token
coverage accounts for **2.76%**. These percentages overlap and must not be added.

This narrows the exact longer-sequence explanation on the exposed development
panel. It does **not** confirm generalization, establish meanings, rule out
nonexact templates or make the groups independent. There were no new predictions,
model changes, captures or network requests. E79 remains an adaptive development
result, and its original gate was not retested.

## Fixed accounting

The [protocol](../experiments/sequence_overlap_v88.md), new code and historical
seals were [hash-bound](../experiments/sequence_overlap_v88.json) before the one
execution. All 13 groups, 98 units, 1,918 target pairs and original token/mask/
boundary rules were retained. Matches use exact E76 forms, never pooled UNK
categories, and only the other twelve groups supply each fold’s training windows.
Both context and target must lie inside the same matching window.

| Exact window length | Covered targets / 1,918 | Changed predictions covered / 311 | Positive gain mass covered | Covered macro contribution | Uncovered macro contribution |
|---|---:|---:|---:|---:|---:|
| 2 | 208 | 172 | 100.00% | +0.117185 | -0.044308 |
| 3 | 16 | 9 | 6.41% | +0.007524 | +0.065352 |
| 4 | 6 | 4 | 2.76% | +0.003235 | +0.069642 |
| 5 | 0 | 0 | 0.00% | +0.000000 | +0.072877 |
| 6 | 0 | 0 | 0.00% | +0.000000 | +0.072877 |
| 7 | 0 | 0 | 0.00% | +0.000000 | +0.072877 |
| 8 | 0 | 0 | 0.00% | +0.000000 | +0.072877 |

Contributions are bits per original target, averaged equally over all thirteen
groups. Each row’s two contributions sum to the unchanged **+0.072877** macro
gain. They are partitions of saved gains, not scores after deleting passages.
The full positive contribution is +0.117373 and the negative contribution is
−0.044496. Counts are distinct evaluation target pairs; the retained occurrence
ledger separately contains **1,178** matching window-occurrence pairs: 1,166
bigrams, ten trigrams and two four-token windows. Multiple training occurrences
never multiply a target’s contribution. The length spectrum is nested, whereas
the local report also retains disjoint capped-maximum bins.

All positive gains fall on bigrams observed in training. This is expected from
E79’s mechanism: an unseen known pair cannot be boosted by its constrained
pair model, and unknown targets retain the unigram probability. It is not an
independent discovery that recurrence exists. The useful additional observation
is how little positive gain coincides with exact sequences of three or more
forms. The absence of a five-token match also excludes longer exact runs within
these same segments, since any such run would contain a five-token window.

## Every group

| Frozen connected group | Targets | Bigram-covered | Trigram-covered | Four-token-covered | Saved gain |
|---|---:|---:|---:|---:|---:|
| accidental_altruist+interstellar_intersubjectivity | 158 | 15 | 0 | 0 | +0.058559 |
| capra_foreword+weber_holomovement | 138 | 21 | 2 | 0 | +0.138918 |
| dark_side_light | 123 | 21 | 4 | 0 | +0.110144 |
| deep_physics_second_law+fake_news_roundup+models_magic | 271 | 17 | 0 | 0 | +0.037023 |
| exalted_deeds+vile_darkness | 144 | 16 | 5 | 3 | +0.067422 |
| gad_seer | 149 | 23 | 0 | 0 | +0.118020 |
| golden_age+secret_symbols | 151 | 20 | 2 | 0 | +0.071643 |
| liber_azazel | 122 | 9 | 0 | 0 | +0.038241 |
| manichaean_hymn+manichaean_roman_texts | 139 | 16 | 0 | 0 | +0.076267 |
| nichiren_images | 146 | 17 | 0 | 0 | +0.084362 |
| religious_architecture | 150 | 16 | 3 | 3 | +0.071018 |
| risk_math+war_algorithm_accountability | 110 | 9 | 0 | 0 | +0.049080 |
| western_esoterism | 117 | 8 | 0 | 0 | +0.026699 |

Zero-coverage groups remain in every macro denominator. Unknowns, zero gains,
negative gains and all unmatched targets remain in the ledger. Empty conditional
means are null. No favorable group, cutoff or retained subset was selected.

## Interpretation and stopping point

Long exact wording repetition accounts for a small part of the saved positive
gain under this measurement. Approximate or discontinuous templates, recurring
function-word patterns, annotation-derived masks, genre, generator rules and
erroneous connected groups remain possible influences. Exact matches themselves
can be ordinary recurring language; they do not establish copying, common source
identity or semantic correctness. This diagnostic supplies no causal estimate of
what a retrained model would do without matched passages.

The 2..8 audit is complete and stopped. Do not delete overlaps, merge groups,
change masks, rescore residuals, tune E79 or request a third listing under this
registration. E77’s failed gate and E79’s development pass remain unchanged.
E85/E87’s zero-new-nomination results and E84’s closed restricted-WARC route
remain intact. Natural semantic benchmark capacity stays **0/4 qualifying works**;
no independent reviewer or untouched confirmation unit was added.

The highest-value next research step still requires a documented new corpus
resource with a bounded cohort selection and credible independent-group capacity.
Another rescore of the same groups cannot supply that evidence. This report
launches no acquisition or model comparison.

## Verification and publication

The separate verifier imports no project parser or prediction code. It enumerates
diagonal equal-token runs rather than looking up indexed windows, reproduces all
1,178 occurrence pairs, and reconstructs every target’s coverage, source offsets,
saved probability binding and gain partition. All 1,918 targets and 311 changed
predictions reconcile to E79. It also checks E76/E77/E79/E87 seals. This is
computational reconstruction, not independent scientific review.

Six synthetic fixtures cover barriers, pair containment, all repeated occurrences,
exact forms, the eight-token cap, negative/zero gains and original group weighting.
**633 workspace tests and 594 isolated-public tests pass**, with the same 39
archive-dependent exclusions. Public main contains code, protocol and aggregate
reports; raw token windows, offsets and per-target ledgers remain on the
local-only evidence branch. Historical sealed files remain unchanged.

Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_sequence_overlap_v88.py
```

Preparation and execution are single-use and refuse to overwrite their paths.
