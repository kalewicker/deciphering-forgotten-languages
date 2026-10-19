# Experiment 44: exact partial English overlap in all six unmatched blocks

This is a new partial-overlap question. Preserve experiment 43's 0/6 whole-block
result, all earlier queries/outcomes and their frozen source representations.
No natural semantic accuracy, opaque passage ancestry or source identity is tested.

Before scoring, freeze quote02 through quote07 from the original v38/v39 ledger,
all target offsets, the complete 12,072-character v42 publisher body, v43 results,
all 43 prior manifests/seals, this registration and new algorithm/fixtures/runner.
Use timestamped preflight and write a frozen six-query ledger before assessment.
Zero network requests or new HTML/PDF extractions. No resegmentation or source
window selection; the whole saved publisher-page body remains the source scope.

Tokenization: each original Unicode `\S+` span is a token. Normalize each with
NFC then casefold, preserving all punctuation, apostrophes, hyphens and word order.
No stemming, punctuation stripping, quote repair, stopwords, gaps, edits or
synonyms. Consecutive tokens can cross whitespace/DOM joins already present in
the frozen body. This is a different declared assay, not a change to v38's
whole-string matcher; old outcomes are never overwritten.

For each of the six fixed queries, enumerate every exact common contiguous-token
run that cannot extend left or right along its query/source diagonal. Keep every
maximal run of at least **8 tokens**, including ties, repeated source occurrences
and overlapping runs; do not choose only the most favorable excerpt. Save the
longest run at any length, even when below threshold. Preserve query/source token
spans, original Unicode character spans, global FL-target spans, normalized token
sequences and exact raw fragments. Coverage is the union of target query token
indices, so overlaps/repeated witnesses cannot inflate it. Aggregate covered/total
tokens descriptively across all six blocks; no percentage is translation accuracy.

Primary descriptive readout: number of the six queries with at least one retained
8-token run; fixed denominator six. Also retain all lengths, run counts and
coverage, including zero/unavailable outcomes. No probabilistic significance,
source uniqueness, direction of copying or statistical independence is inferred
from a threshold hit. The threshold is an engineering reporting cutoff.

Controls are outside the six-query denominator: original quote00 must have a run
of at least max(8, its token count minus 2), allowing only its known enclosing
boundary punctuation difference; quote01 must remain below eight tokens; the
eight fixed nonce tokens in JSON must have longest run zero; reversed original
quote00 tokens must have no qualifying eight-token run. If any control fails,
the primary readout is null/invalid while raw observations remain saved. No retry,
threshold change or alternative control follows scoring.

Verify against a separately implemented suffix-length dynamic program that finds
maximal right ends, reconstructing every run and coordinate. Test ties/repeats,
overlapping diagonals, exact threshold, order/gaps/punctuation/apostrophes, Unicode
offsets and unavailable separation before scoring. Check all 43 old runs/seals.
No opaque passage, meaning, immediate source identity, independent review,
original quotation provenance or untouched work is admitted; semantic metrics
and scientific acceptance remain null.

Write immutable evidence/report, interpretation, verification and seal, run
appropriate full/public tests, checkpoint evidence locally, commit/push public
main, and stop. Any broader alignment or interpretation needs its own scope.
