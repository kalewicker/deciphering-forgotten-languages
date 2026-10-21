# E79: one constrained context model on the frozen development panel

E78 identified penalties on unseen pairs after observed contexts and substantial
unknown-category effects. Test one fixed alternative, not a parameter search.
The design is informed by E77/E78's exposed results: it is development evidence,
not a fresh confirmatory test and not a repair of E77's failed registration.
Freeze protocol, code and inputs before fitting. Fixture checks precede scoring.

## Fixed model and falsifiable question

Can context supported across training groups improve known-word predictions
without gaining from pooled unknown targets? Keep E77's unigram, training-only
vocabulary (count >=2), 13 folds, 98 units, 1,918 actual target pairs, barriers,
mask, target ordering and all 99 original within-segment shuffle orders unchanged.
No new texts, split, controls, word forms, smoothing search or group selection.

Let U be E77's add-0.5 training unigram and q=1-U(UNK). Always set P(UNK|h)=U(UNK).
For a known context h, count only transitions to KNOWN target categories: n(h,w),
N(h)=sum over known w, and G(h)=number of training groups with >=1 such outgoing
transition. Eligibility requires h != UNK, N(h)>=5 and G(h)>=2. The thresholds
are prespecified conservative design choices, not estimated reliability or
optimized values. UNKNOWN contexts and all ineligible contexts return U exactly.

For eligible h and known w:
  R(w|h) = (n(h,w) + 10*U(w)/q)/(N(h)+10)
  P(w|h) = q*(0.5*U(w)/q + 0.5*R(w|h)).

This distributes the original known-word mass q while blending the conditional
unigram and smoothed conditional pair distribution equally. Unknown target mass
is unchanged, every probability remains positive, and the full alphabet sums to
one. For zero-count known pairs in an eligible context, P/U is
0.5 + 5/(N(h)+10), hence their loss penalty is less than one bit. These are
mathematical constraints, not performance guarantees. Boosting some known words
still requires reducing others. No gating uses the actual evaluation target.

Use only the OTHER 12 groups to form vocabulary, counts and G(h). For every saved
shuffle draw, independently recompute counts and eligibility from its training
sequences; reuse original training vocabulary/U (histograms are unchanged).
Never transfer observed-model support flags into shuffled models. Test sequences
remain actual unshuffled text. All safeguards are one combined intervention;
this experiment cannot identify their separate causal effects.

## Metrics, gate and exposure

Retain E77's fixed five-component gate: macro gain >=0.05 bits/target; positive
gain in >=10/13 groups; >=20 known targets per group; known-target macro gain >0;
conditional control rank <=0.05 with all 99 draws and ties. Report every group,
full control distribution, unknown burden and token-weighted secondary gain.
The rank is descriptive on a dependent, adaptively studied corpus, not a
population p-value. The original E77 gate remains failed whatever E79 does.

Additional engineering requirements: normalized finite positive distributions,
unknown target probabilities equal their original unigram probabilities,
unknown/ineligible contexts back off exactly, eligibility is training-only, and
all original targets/controls remain. Any violated requirement makes the run
invalid; do not salvage it through an after-result repair. Preserve original
known-target and full denominators; unknown targets stay and contribute zero gain.
Record eligible evaluation-context counts per group, model support counts and
all per-target observed/control probabilities. Compare each group's gain with
E77 descriptively, without adding a success criterion or testing more variants.

## Verification and stop

Test mass conservation, exact fallback, unknown neutrality, group support,
training-only vocabulary and unseen-pair penalty bound before freezing. A separate
verifier must reconstruct grouped counts and eligibility and every probability
via rational arithmetic without importing the new predictor. Reconstruct every
metric, control and gate; check E76/E77/E78 seals. Single preparation and scoring
attempt, immutable outputs, no feedback or threshold adjustment.

Stop after this one model comparison, pass or fail. A failure closes this
combined rule on this panel; do not sweep cutoffs, mixture weights or prior mass.
A pass establishes only conditional next-category prediction on exposed masked
excerpts and requires genuinely new reserved material for confirmation. No broad
model expansion is authorized by either outcome. No semantic/source identity,
independent review or untouched-unit admission; semantic benchmark stays 0/4.
