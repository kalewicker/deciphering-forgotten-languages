# E79: constrained context prediction passes the development gate

The single registered alternative passes all five development criteria:
**0.072877 bits/target** macro gain over the unchanged unigram, positive gains in
**13/13 groups**, and **0.146267 bits** macro gain on known targets. Unknown-target
probabilities are fixed to the unigram and contribute exactly zero gain.
The observed result beats all 99 saved-order shuffled-training controls.

This is a useful result on the **same exposed development panel**, not independent
confirmation. E78's diagnosis informed the design. E77's original model, predictions
and failed gate remain intact. No meanings, source identities, independent reviews
or untouched units are admitted; natural semantic benchmark capacity remains 0/4.

## Registered model and unchanged comparison

The [protocol](../experiments/context_guard_v79.md) and
[hash-bound configuration](../experiments/context_guard_v79.json) were frozen after
fixture checks and before this one scoring attempt. All E77 folds, 98 retained
units, 1,918 targets, training-only vocabularies, unigram probabilities, masks,
barriers and 99 original shuffle orders were retained.

The new rule has three linked safeguards. Unknown target mass stays at its
unigram value; unknown contexts fall back to unigram. A known context can modify
known-word probabilities only with at least five known-target transitions from
at least two training groups. For an eligible context, the model splits the
known-word mass equally between conditional unigram probabilities and a pair
model smoothed with a fixed prior mass of ten. These thresholds and weights were
prespecified design choices, not optimized estimates of reliability.

The resulting probability distribution stays normalized and positive. An unseen
known-word pair in an eligible context incurs less than a one-bit penalty.
Those constraints do not guarantee an improvement, and boosting some known words
still reduces probability for others. No evaluation target determines context
eligibility. Each shuffled model recomputes its own counts and group-support gate
from shuffled training sequences; it never inherits observed-model eligibility.

All safeguards changed together, so their separate causal effects are not
identified. There was no parameter sweep, alternative vocabulary, favorable-group
selection, new seed or replacement control.

## Full gate

| Criterion | Required | Observed | Result |
|---|---|---|---|
| Equal-group mean gain | >=0.05 bits/target | 0.072877 | Pass |
| Groups with positive gain | >=10/13 | 13/13 | Pass |
| Known targets in every group | >=20 | 46–89 | Pass |
| Known-target macro gain | >0 | 0.146267 | Pass |
| Conditional control rank | <=0.05 | 0.01 | Pass |

Control macro gains range from **-0.039412 to +0.008919** bits/target. All 99
remain in the denominator, including any identity/repeated orders. The corrected
rank is 1/100. This is a descriptive rank on dependent folds and an adaptively
studied corpus, not a calibrated population p-value. The secondary token-weighted
gain is 0.071363 bits/target.

## Every group

Positive gain means lower loss than the unchanged unigram. Eligible known pairs
are targets whose known context passed the training-only support rule AND whose
target was known. Other targets keep the unigram probability.

| Group | Pairs | Eligible known pairs | Unigram loss | New loss | Gain | Known gain | Gain change from E77 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Accidental Altruist / intersubjectivity | 158 | 19 | 3.903915 | 3.845356 | 0.058559 | 0.125031 | -0.033996 |
| Capra / Weber | 138 | 25 | 4.481506 | 4.342588 | 0.138918 | 0.255610 | -0.034183 |
| Dark Side of Light | 123 | 30 | 4.001155 | 3.891010 | 0.110144 | 0.205268 | -0.028155 |
| Deep physics / fake news / models of magic | 271 | 21 | 3.288624 | 3.251602 | 0.037023 | 0.118036 | -0.089653 |
| Exalted deeds / vile darkness | 144 | 19 | 4.038902 | 3.971480 | 0.067422 | 0.151699 | 0.020866 |
| Gad the Seer | 149 | 32 | 4.499769 | 4.381749 | 0.118020 | 0.222595 | -0.117557 |
| Golden Age / secret symbols | 151 | 35 | 4.589777 | 4.518134 | 0.071643 | 0.121552 | 0.080213 |
| Liber Azazel | 122 | 29 | 5.176813 | 5.138572 | 0.038241 | 0.062206 | 0.218680 |
| Manichaean hymn / Roman texts | 139 | 25 | 3.943448 | 3.867180 | 0.076267 | 0.153640 | -0.057241 |
| Nichiren images | 146 | 29 | 4.471408 | 4.387046 | 0.084362 | 0.153960 | 0.191926 |
| Religious architecture | 150 | 18 | 3.938790 | 3.867772 | 0.071018 | 0.156657 | -0.028457 |
| Risk / war accountability | 110 | 14 | 4.094252 | 4.045173 | 0.049080 | 0.117364 | 0.233303 |
| Western esoterism | 117 | 15 | 4.117641 | 4.090942 | 0.026699 | 0.057849 | -0.016421 |

The rule has eligible contexts at **763/1,918** evaluation positions, but only
**311** also have known targets and can change predictions. All 994 unknown
targets retain exactly their unigram probability; the remaining known targets
with unsupported/unknown contexts also fall back. The full 1,918 denominator
and all 924 known targets remain in the metrics. Eligibility is an opportunity
to alter probabilities, not a claim that every such prediction improves.

All thirteen groups beat the unigram, but only **5/13** improve their full-target
gain compared with E77. The other eight give up some aggregate gain while removing
unknown-target effects and constraining context updates. The primary macro gain
rises from 0.046775 to 0.072877, and known-target macro gain changes from -0.066232
to +0.146267. This descriptive comparison is not an independent replication or
an ablation identifying which safeguard caused the change.

## Scope and stopping point

This supports transferable next-category regularity under this fixed representation
and training procedure on the exposed panel. Indexed-excerpt provenance,
annotation-based language/source grouping, short or approximate overlaps, copied
residues, templates, genre and generator rules remain possible influences. The
mask itself was derived from the full previously exposed annotation inventory.
Training-only model fitting does not turn that inventory into untouched data.
Positive category prediction does not establish grammar or recover meanings.

Stop this model comparison here. Do not tune the support cutoffs, mixture or prior
mass, and do not add further features based on these scores. The next substantive
step would be to preregister a bounded acquisition/eligibility process for genuinely
new reserved material, selected without prediction outcomes, followed by a separate
frozen confirmation protocol. It must preserve this rule and handle insufficient
new material as a feasibility failure. Another rescore of these same groups would
not confirm generalization. This report launches neither acquisition nor scoring.

The independent-review route remains relevant to meanings/source relationships;
it is separate from observable-token confirmation. E62/E70 discovery routes and
synthetic feature expansion remain stopped. E77's failed gate stays failed.

## Verification and preservation

The independent verifier imports no E79 predictor. It reconstructs segments,
shuffle orders, vocabulary, grouped counts, eligibility and full distributions
using exact rational arithmetic, then checks saved probabilities and every
observed/control metric. Unknown neutrality and fallback are exact checks;
normalization is exact in the verifier. Floating-point predictions agree within
1e-12 with the independent probabilities. All E76/E77/E78 seals remain intact.

Six fixture tests cover mass conservation, unknown neutrality, exact fallback,
minimum count/group support, unseen-pair penalty bounds and training-only
vocabulary. **577 workspace tests and 538 isolated-public tests pass**, with the
same 39 archive-dependent exclusions. The public receipt records verification
counts. Raw vocabularies, target ledgers and predictions stay on the local-only
evidence branch; public main contains code, protocol and small reports.

Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_context_guard_v79.py
```

Preparation and scoring are single-use; do not overwrite sealed paths.
