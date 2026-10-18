# Experiment 31: synthetic mechanism and identifiability calibration

Register and seal before generating the full fixtures or scores. Calibrate the unchanged v30 ten-token equality-pattern scorer/threshold on known synthetic lineage, without another natural-source attempt. Preserve v30's failed criterion, boundaries, mask and every earlier artifact. No FL/source text, dictionary, linguistic gloss, model, PDF processing, network, new source, external message or natural-target rescore is used. Synthetic generator truth is not semantic gold for FL.

## Fixed factorial corpus and oracle separation

Use ten symbolic profiles crossed with four fixed keys (11,29,47,83), for 40 synthetic parents. Six profiles are length 64 with class IDs given by integer SHA-256(`v31|profile|{profile_index}|{i}`) modulo vocabulary sizes 6,8,10,12,16,24. Four diagnostic profiles are all-unique length64, one repeated class at indices divisible by3 with unique other classes length64, an eight-token short profile [0,1,0,2,1,3,4,5], and a length64 vocabulary8 hash profile with dense barriers. This is a convenience factorial fixture, not a sampled natural-language distribution. Do not select profiles/keys after feature counts.

For all but the dense-barrier profile, positions with (i+1) divisible by17 are explicit blocked anchor tokens; dense barriers use divisor5. The barrier form is `copiedanchor{(i//barrier_period)%3}`. Unblocked source forms are `sourcep{profile_index}k{key}word{class_id}`. Barriers are copied literally to queries and stay hard barriers. They do not borrow any natural anchor or new natural evidence. Every public token has exact synthetic text offsets and a blocked flag.

Cross each parent with five mechanisms, retaining all 200 queries:

1. Bijective renaming: one opaque alias per unblocked source type.
2. Insertion: bijective rename plus a distinct unblocked insertion after every seventh source position, including a final seventh position if present. Insertions have null source origin.
3. Deletion: omit source positions whose one-based index is divisible by7; keep all other source origins.
4. Contextual forms: alternate two aliases by zero-based occurrence parity of each unblocked source type. Barriers do not change their literal forms.
5. Local reordering: swap source-origin indices (6,7),(13,14),… whenever both exist, then apply the bijective alias.

The alias is `opaquecode` plus the first 20 hex digits of SHA-256(`v31|alias|{profile_index}|{key}|{source_form}|{parity}`), parity0 except contextual variants. Assert alias injectivity over each parent's distinct source forms/parities. Inserted forms are `insertedp{profile_index}k{key}at{i}`. Preserve full alias tables, query-token-to-parent-origin lists, deleted source indices and every generated surface in a separate oracle. The scorer receives public views and panels only; it never reads origins, mechanism names, true-parent labels or keys to make a decision. Generator code is public and frozen; these are not secret-key held-out language trials.

## Fixed distractors and 1,000 panels

For each parent create five distractors, all at the parent's original token count/barrier positions:

- Unique filler: one different unblocked form per position.
- Frequency-preserving shuffle: unblocked source indices sorted by SHA-256(`v31|shuffle|{base_id}|{i}`), index breaking ties, assigned to ascending unblocked positions. Identity orders, if any, remain.
- Different-pattern stream: unblocked class ID SHA-256(`v31|negative|{base_id}|{i}`) modulo12, with distinct lexical namespace. Known generated non-parent status does not imply a random negative will lack short matching patterns.
- Repetition-equivalent impostor: a new one-to-one alias for every unblocked parent form in a disjoint namespace, with barriers unchanged. It is a constructed non-parent under the recorded true key/lineage, while an alternative unknown key would also fit it. Preserve its equivalence certificate; do not call it independent natural material.
- Anchor frame: copy barrier tokens and use unique unblocked fillers elsewhere.

Create five panels per query: present (slot0 parent, slots1–3 unique/shuffle/different-pattern); absent (slots1–3 only); collision (present plus slot4 impostor); impostor-only (slot0 impostor plus the same slots1–3); anchor-frame (slot0 frame plus the same slots1–3). Total 1,000 panels, 200 of each scenario, with all 200 query parents/mechanisms retained. Public case/view IDs are deterministic hashes, and public slots are generic. Public metadata is not a feature. True parent slots are slot0 in present/collision, null in the other scenarios. Gold labels and public cases remain separate files.

Before any pair/panel scoring, freeze feature availability for all public views: number of eligible fingerprint types, and whether at least two are available. Save all 40 parent/impostor complete fingerprint-profile equivalence certificates (signature and occurrence counts) and the 200 paired present/impostor-only case IDs. Do not exclude a query with insufficient features. Report all-case and feature-conditional denominators separately. Preflight feature counting is not query–candidate scoring.

## Unchanged readout, metrics and criteria

Use v30's exact ten-token windows, at least four distinct types/two repeated types, global blocked-position barriers, distinct shared fingerprint count and minimum two shared types. Preserve all pairwise fingerprint witnesses, scores, top ties and abstentions. Apply v30's unique qualifying top decision independently to each panel. No tuning, learned key, edit-tolerant alignment or new score is added. Score each query against its true parent separately as a paired sensitivity measurement, even when that parent is absent from a particular panel; this does not inject it into the panel decision.

For each mechanism report all 40 paired qualifications, all 40 present-panel true-parent recoveries, wrong nominations and abstentions; also report feature-conditional counts with their availability denominator. In every scenario report the full 200-case denominator and count correct-parent nominations, non-parent nominations and abstentions. Conditional origin-label correctness is synthetic only. All 600 absent/impostor-only/anchor-frame panels are rejection trials; separately count frame selections versus other distractor selections. All 200 collision panels are ambiguity/abstention trials; a higher-scoring third distractor still counts as a failure to abstain.

The synthetic candidate-localization admission criterion requires: all feature-available bijective paired positives qualify (with nonempty eligible denominator); all feature-available bijective present panels recover their true parent; all 600 rejection panels abstain; all 200 collision panels abstain; and all feature-unavailable panels abstain. Preserve every failed component. Altered mechanisms' sensitivity is descriptive rather than an assumed guaranteed capability. Report overall sensitivity including unavailable cases; do not label conditional success as universal power.

Independently verify the observational non-identifiability experiment: all 200 present/impostor-only panel pairs have identical candidate-slot fingerprint features, pairwise scores and decisions despite different recorded true-parent availability. These are identical observations for this feature representation, not identical raw strings or a theorem about all possible methods. A decision that names slot0 in both worlds recovers a recorded parent in one and a constructed non-parent in the other. No score threshold can separate those equal-feature worlds while keeping a nonempty nomination there. Explicit ties can force abstention; an absent equivalent alternative cannot be detected from these features alone.

Engineering calibration completion requires exact generation/oracle/offset replay, all 1,000 cases scored, all 40 equivalence certificates and all 200 paired-world decision-equality checks. It is separate from candidate-localization admission and natural scientific acceptance. Even a passed synthetic criterion would not admit a natural source identity, word meaning, independent review or untouched FL test unit.

## Verification and stopping rule

Seal registration, inputs and all code before preparation; freeze public cases, oracle, availability/certificates and benchmark before execution. Refuse existing outputs. Use a separate independent generator/lineage reconstruction and pairwise-equality formulation to replay every availability profile, every witness, parent score, panel score/decision, counterfactual equality, metric and gate; verify all 30 prior run/seal inventories. Tests cover exact aliases/origins, insert/delete/reorder/context mechanisms, barriers, shared-type deduplication, unavailable features, ambiguity ties, equal-feature worlds, full denominators and raw offsets.

Stop at this assay, including failed sensitivity/rejection components. No parameter or fixture changes after scoring. Keep natural semantic metrics/scientific acceptance null and source identity/semantic label/independent-review/untouched admissions zero. This experiment calibrates a fixed representation; it does not retry v30 or validate general translation.
