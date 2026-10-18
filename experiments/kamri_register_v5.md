# Experiment 5 registration: scoped lexical aliases

Registered 2026-09-30 before model execution or fresh correspondence scoring.

## Question and fixed panels

Test whether three proposed alternate-register function forms improve the unresolved Misinfons development passage, and whether restricting their use avoids applying them to ordinary Kamri. This is a structural alignment and lexical-evidence engineering experiment, not semantic translation validation.

All nine real works from v3a and all 48 v4 synthetic cases are development material. No v4 synthetic case is fresh in this experiment. The unchanged v1 lexicon remains the baseline. No content-word induction, automatic claim promotion, or other register substitutions are allowed.

Fresh selected denominator is two new source works nominated by the existing public Kamri report: (1) Fritjof Capra's foreword to Metaphors of Consciousness, opening Reality and Other Mental Devices (2019-07-22); (2) Mark C. Langston's The Accidental Altruist, opening Altruistic Beacons (2019-07-29). Select the opening complete Kamri sentences up to 180 whitespace words, stopping at the first embedded English paragraph or indexed excerpt limit. Preserve extraction drop caps with explicitly recorded joins. Source scope is the publicly available corresponding chapter/front matter, capped at 2,000 word tokens from the opening chapter prose; remove headers and bibliography, retain source prose. Save actual scope and transformations. These source works differ from all nine development works.

Acquisition is finite: publisher page plus one linked public preview/front matter route per work, and one exact-title discovery query for a public author/institution copy. Do not bypass access restrictions. Missing, partial, or unauditable inputs remain in the selected denominator; do not replace either work. A missing corresponding source means reference edges are unavailable, not zero. Do not claim selected-sample alignment recall with incomplete reference coverage. Indexed FL is explicitly not a raw/current-page snapshot. Retain source URLs, acquisition failures, saved bytes, and hashes before scoring.

## Frozen proposal and development audit

The public report proposes ńańi -> of, daċċęįš -> and, tawwdan -> that for Misinfons. Treat these as external proposals only. Before evaluation, audit their occurrences against the existing manually reviewed Misinfons/source spans. Use exact equal-token-length positional projections where possible; otherwise record source-span word presence and compatible ordinal context separately. Save positive, contradictory, and unresolved evidence. Do not manufacture independent support: every observation comes from one source work. Aliases are explicitly register-scoped experimental hypotheses, never entries satisfying the original two-independent-work eligibility rule.

All three proposals remain fixed regardless of development results; compare them as a bundle and preserve contradictions. A marker gate activates only when the query contains at least two distinct proposed alias forms and at least three total occurrences. Detection uses only normalized query tokens, without title, source identity, answer, or reference edges.

## Three matched variants

1. baseline: unchanged v1 eligible predictions.
2. universal_aliases: override those three forms in every query, exposing the risk of universal application.
3. gated_aliases: apply those overrides only when the fixed marker gate activates.

Each uses the v4 token-mass local aligner, protected boundaries, up-to-2:2 blocks, ordered token decoder, structural/lexical blend 0.60/0.40, floor 0.72, and all other v4 parameters unchanged. Record override origin and gate counts. No lexical evidence from fresh inputs or inferred alignments trains any variant. The original text and token offsets never change.

Rank the nine unchanged real source packets plus available selected fresh packets. Freeze candidates and reference edges before executing. Calibrate each variant using maximum wrong-work strength over the nine development queries in this expanded candidate pool plus 1e-6. Fresh query outcomes never set thresholds. Admission requires threshold, margin >1e-9, and at least three linked FL atoms. Source-absent controls remove every candidate edition of the corresponding work.

## Measures and controls

- Development: Misinfons rank/admission/conditional and retrieved edges; frozen-prediction coverage; alias audit; changed predictions and edge outcomes on the eight other works. Keep all failures.
- Fresh: unique correct top-1/2 selected, correct admissions/2 selected, available/reference-covered counts, retrieved and conditional edge precision/recall on auditable cases only, source-absent false admissions/2 selected with availability explicitly reported. No claim of transfer to a second alternate-register work: the fresh works may use ordinary Kamri.
- Save all three variants, candidate scores, margins, paths, spans, inferred edges, predictions, source-absent decisions, thresholds, and input/code/output hashes.
- Use 20 shared nonidentity FL atom permutations per available real query, seed 5731; repetitions allowed, identity forbidden. If fewer than two atoms, mark unavailable. Recompute windows. Report descriptive exceedances and actual denominator, not p-values.
- Repeat v4 synthetic cases only as development regression diagnostics for alias activation and changed predictions; do not report them as fresh confirmations and do not use them to select thresholds.
- One final execution after implementation tests and source audit; no tuning or fresh-case replacement afterward. Any subsequent model change requires a new experiment.

## Limits

Single-work alias evidence, nomination bias, tiny source-known evaluation, uneven public source availability/scopes, indexed FL text, analyst structural labels, and the gate's unvalidated register classification. These tests cannot recover or validate a general grammar, establish content-word meanings, or demonstrate alternate-register transfer with only the existing Misinfons development example.
