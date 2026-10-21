# E78: losses concentrate on unseen pairs after seen contexts

The read-only decomposition reproduces E77's failed result and identifies its
arithmetic source. **291 known-word targets** follow a context with training
observations but have no occurrence of that specific context-target pair. Their
negative contribution outweighs the positive contribution from **633 known-word
targets** whose pair did occur. This is attribution of saved losses, not evidence
that a different model would improve them.

The [registration](../experiments/order_diagnosis_v78.md) and
[hash-bound configuration](../experiments/order_diagnosis_v78.json) fixed the
partition before computing it. E77 aggregate results were already exposed.
All 13 groups, 1,918 targets and 99 controls were retained. No new predictions,
model fitting, corpus changes, acquisitions or parameter comparisons occurred.

## Contributions to the original macro gain

Each cell's gain sum is divided by its group's full target count, then averaged
across all 13 groups. Empty cells contribute zero. Thus the observed column below
sums to E77's **0.046775 bits/target**. These are additive contributions, not cell
means or independently validated subgroup scores. Control cells use the same
membership defined from original training counts; the last column averages the
99 saved control contributions. Every individual draw is preserved locally.

| Target | Context | Original training support | Targets | Observed contribution | Mean control contribution |
|---|---|---|---:|---:|---:|
| known | known | unseen context | 0 | 0.000000 | 0.000000 |
| known | known | unseen pair | 233 | -0.183515 | -0.125237 |
| known | known | seen pair | 194 | 0.194381 | -0.048378 |
| known | unknown | unseen context | 0 | 0.000000 | 0.000000 |
| known | unknown | unseen pair | 58 | -0.181086 | -0.064136 |
| known | unknown | seen pair | 439 | 0.130993 | -0.010663 |
| unknown | known | unseen context | 1 | 0.000000 | 0.000000 |
| unknown | known | unseen pair | 56 | -0.011536 | -0.000812 |
| unknown | known | seen pair | 545 | 0.124307 | 0.027328 |
| unknown | unknown | unseen context | 0 | 0.000000 | 0.000000 |
| unknown | unknown | unseen pair | 0 | 0.000000 | 0.000000 |
| unknown | unknown | seen pair | 392 | -0.026770 | 0.013765 |

For known targets, the two unseen-pair cells contribute **-0.364601** bits to
the full-denominator macro score; seen-pair cells contribute **+0.325374**.
The net known-target contribution is **-0.039226**. Unknown-target cells add
**+0.086001**, yielding the original overall +0.046775. The original conditional
known-target macro gain remains **-0.066232**: its denominator is known targets
within each group, so it differs from the additive full-denominator contribution.

Only **one** target has a context with zero outgoing training pairs. Its gain is
exactly zero under backoff. The failure is therefore not accounted for by many
unseen contexts. For a seen context with an unseen pair, E77's equation implies:

`gain = log2(10 / (context_count + 10))`

This is always negative. The verifier checks that identity for every applicable
target. Among known targets, 58 unseen pairs follow the pooled unknown context;
those 58 alone contribute -0.181086, compared with -0.183515 from 233 unseen pairs
following known contexts. Their different penalties reflect original outgoing
context counts. This does not establish the causal effect of removing unknown
pooling or changing prior strength; neither counterfactual was tested.

## Unknown status and all groups

There are **924 known targets**, **160 training-singleton targets**, and **834
training-absent targets**. The latter two form E77's 994 unknown targets. Status
is fold-specific training exposure, not meaning knowledge; repeated occurrences
remain targets rather than distinct word types. Pooling into unknown never
predicts the absent form's spelling.

| Group | Known | Singleton | Absent | Known contribution | Unknown contribution |
|---|---:|---:|---:|---:|---:|
| Accidental Altruist / intersubjectivity | 74 | 7 | 77 | -0.042188 | 0.134743 |
| Capra / Weber | 75 | 13 | 50 | 0.084141 | 0.088960 |
| Dark Side of Light | 66 | 7 | 50 | -0.002019 | 0.140318 |
| Deep physics / fake news / models of magic | 85 | 23 | 163 | 0.072015 | 0.054661 |
| Exalted deeds / vile darkness | 64 | 25 | 55 | -0.020735 | 0.067291 |
| Gad the Seer | 79 | 13 | 57 | 0.137533 | 0.098044 |
| Golden Age / secret symbols | 89 | 7 | 55 | -0.084807 | 0.076237 |
| Liber Azazel | 75 | 6 | 41 | -0.304391 | 0.123952 |
| Manichaean hymn / Roman texts | 69 | 7 | 63 | -0.001162 | 0.134670 |
| Nichiren images | 80 | 12 | 54 | -0.199423 | 0.091859 |
| Religious architecture | 68 | 18 | 64 | 0.071215 | 0.028260 |
| Risk / war accountability | 46 | 10 | 54 | -0.174447 | -0.009776 |
| Western esoterism | 54 | 12 | 51 | -0.045677 | 0.088797 |

Each row's two contributions sum to that group's original gain. No group was
removed. The observed and all 99 control macro scores reconstruct exactly within
floating-point tolerance. E77's original conditional rank of 0.01, 9/13 positive
groups, gain thresholds and failed combined gate are unchanged. Control separation
does not override the known-word deterioration.

## Decision and limits

This closes the diagnosis. The next design question is whether a prespecified
way of accounting for the reliability of training context counts can preserve
useful observed associations without excessive penalties on unseen pairs. This
report does not select a new model, smoothing constant, vocabulary cutoff or
subgroup; none was tested. Any proposal must fix training-only choices and
unknown-word accounting before scoring, retain known-target safeguards and all
groups, and be presented as new development work rather than a repair of E77's
consumed registration. Do not begin model expansion or parameter searches on the
strength of this accounting result alone.

The small, previously exposed indexed excerpts, conservative incomplete masks,
annotated language labels and possible templates/copying remain limitations.
The diagnostic establishes neither grammar nor opaque meanings. It admits no
source identity, independent review or untouched unit. The separate natural
semantic benchmark remains **0/4 qualifying works**. E62/E70 and the stopped
synthetic feature programme stay closed.

## Verification and preservation

A separate implementation imports neither the E78 accounting functions nor the
E77 model. It reconstructs training counts, every category/support assignment,
raw offset binding, all 191,800 observed/control gain values, all 156 group cells,
every fold denominator and every macro/control contribution. Log-ratio and
log-difference formulations agree. It confirms both backoff identities and
reproduces the original known-target score and failed gate.

Six fixture tests cover absence/singleton status, support categories, zero-gain
backoff, unseen-pair penalties, empty cells and unequal group weighting.
**571 workspace tests and 532 isolated-public tests pass**, with the same 39
archive-dependent exclusions. All E76/E77 sealed files remain unchanged.
Generated ledgers stay in the local-only evidence archive; code, registration
and small reports are public.

Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_order_diagnosis_v78.py
```

Preparation/execution are single-use; do not overwrite sealed output paths.
