# E77: small overall context gain, failed development gate

The fixed preceding-word model improves average next-category loss by
**0.046775 bits per target** over the unigram baseline, but the registered
combined gate **fails**. Only **9/13 groups** improve, and known-target-only
macro gain is **-0.066232 bits**: the context model is worse on those targets.
No model, smoothing, vocabulary, mask or threshold was adjusted after scoring.

This is the first prediction test in the user-authorized monolingual pivot.
The [protocol](../experiments/word_order_v77.md) and
[configuration](../experiments/word_order_v77.json) froze E76's 13 eligible groups,
98 units, 1,918 target pairs, code and all 99 control orders before fitting.
Each group was evaluated using models fitted only to the other 12 groups.
All material remains exposed development excerpts, not untouched evaluation.

## Registered decision

| Component | Required | Observed | Result |
|---|---|---|---|
| Equally weighted group mean gain | >=0.05 bits/target | 0.046775 | Fail |
| Groups with strictly positive gain | >=10/13 | 9/13 | Fail |
| Known targets in every group | >=20 | 46–89 | Pass |
| Mean gain on known targets | >0 | -0.066232 | Fail |
| Conditional shuffle rank | <=0.05 | 0.01 | Pass |

The observed model beats all 99 shuffled-training macro gains, which range from
-0.292848 to -0.112916 bits/target. The corrected rank is 1/100, including the
observed case. This is a descriptive comparison with the fixed controls, not a
calibrated population p-value. Folds share training data and are dependent.
The controls preserve each segment's token histogram and length but change
endpoints and pair associations. They challenge the usefulness of actual ordering
for this model; they do not distinguish grammar from templates or generator rules.

The secondary token-weighted gain is 0.057823 bits/target. It does not replace
the preregistered equal-group measure or rescue the failed gate.

## All thirteen groups

Losses are bits per target; positive gain means the context model improves over
the unigram. Known-target gains use the original full-alphabet probabilities on
that subset, without renormalizing to known words.

| Group | Pairs | Unknown targets | Unigram loss | Context loss | Gain | Known-target gain |
|---|---:|---:|---:|---:|---:|---:|
| Accidental Altruist / intersubjectivity | 158 | 84 | 3.903915 | 3.811360 | 0.092555 | -0.090078 |
| Capra / Weber | 138 | 63 | 4.481506 | 4.308405 | 0.173101 | 0.154820 |
| Dark Side of Light | 123 | 57 | 4.001155 | 3.862856 | 0.138299 | -0.003763 |
| Deep physics / fake news / models of magic | 271 | 186 | 3.288624 | 3.161949 | 0.126676 | 0.229600 |
| Exalted deeds / vile darkness | 144 | 80 | 4.038902 | 3.992346 | 0.046556 | -0.046653 |
| Gad the Seer | 149 | 70 | 4.499769 | 4.264192 | 0.235577 | 0.259398 |
| Golden Age / secret symbols | 151 | 62 | 4.589777 | 4.598347 | -0.008570 | -0.143886 |
| Liber Azazel | 122 | 47 | 5.176813 | 5.357252 | -0.180438 | -0.495142 |
| Manichaean hymn / Roman texts | 139 | 70 | 3.943448 | 3.809940 | 0.133508 | -0.002341 |
| Nichiren images | 146 | 66 | 4.471408 | 4.578972 | -0.107564 | -0.363946 |
| Religious architecture | 150 | 82 | 3.938790 | 3.839315 | 0.099475 | 0.157091 |
| Risk / war accountability | 110 | 64 | 4.094252 | 4.278476 | -0.184224 | -0.417156 |
| Western esoterism | 117 | 63 | 4.117641 | 4.074521 | 0.043120 | -0.098966 |

**994/1,918 targets (51.8%)** and 889 contexts map to the reserved unknown
category. Vocabulary was defined separately in each fold using training forms
with at least two occurrences; training singletons also map to unknown. Assigning
high probability to that category does not predict an unseen spelling or meaning.
The known-target safeguard prevents a small aggregate gain from being presented
as successful prediction of actual known word forms. Overall gain, control
separation and known-target deterioration are all retained as distinct outcomes.

## What ran and what the result supports

The unigram uses add-0.5 smoothing. The context model adds a fixed ten-token
unigram prior to within-segment pair counts and backs off exactly for unseen
contexts. No scoring crosses an E76 mask, punctuation, numeric or unit boundary.
Singleton segments contribute to training token counts but supply no targets.
The model predicts an actual stored next-token category from its actual preceding
category; it is not free-running generation or translation.

All 99 deterministic within-segment permutations were stored before scoring,
including identities and any repeated orders. The same draw was reused across
folds, restricted to each fold's training groups. Original and shuffled models
have identical training unigram distributions and vocabularies. Test sequences
were never shuffled. Each target's original UID/token indices and all 100 context
probabilities plus its unigram probability are retained locally.

The frozen corpus already used full-inventory English-field literal masks and
exposed selection/grouping. No test frequencies entered model fitting, but this
is not a claim of an entirely unexposed data-processing pipeline. Indexed
excerpt provenance, incomplete masks, unverified variety labels, short overlaps,
templates and undeclared connections remain limitations inherited from E76.
No source identity, opaque meaning, independent review or untouched unit is
admitted. The natural semantic benchmark remains 0/4 qualifying works.

## Stop and next decision

This closes the registered model comparison with its gate failed. Do not tune
smoothing, change vocabulary cutoffs, add features, select favorable groups or
expand the corpus to obtain a pass under this registration. The result does not
establish that the text is meaningless or that every context model would fail.

The useful next question is a bounded read-only diagnosis of the saved losses:
how much of each group's result comes from known versus unknown target/context
categories, and whether the known-word penalty reflects unseen contexts or
observed training associations. Such a diagnosis needs its own fixed scope,
must retain all groups and original predictions, and cannot change this outcome.
It should precede any proposal for a new model; it is not launched here.

## Verification and preservation

A separate implementation, importing none of the E77 model/runner functions,
reconstructed segments, shuffle orders, training-only vocabularies, category
counts and every probability using independently formulated arithmetic. All
**191,800 context probabilities and 1,918 unigram probabilities** agree, as do
all fold metrics, controls and gate components. E76's seal remains intact.

Six new fixture tests cover hard barriers, training-only vocabulary/unknowns,
normalization/backoff, control histograms, known-target accounting and macro
weighting/ties. **565 workspace tests and 526 isolated-public tests pass**, with
the same 39 archive-dependent exclusions. Public main contains code, protocol
and small reports; raw vocabulary, target ledgers and predictions remain local.

Read-only verification requires the local archive:

```sh
.venv/bin/python scripts/verify_word_order_v77.py
```

Preparation and scoring are single-use and must not overwrite their sealed paths.
