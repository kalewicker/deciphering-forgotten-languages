# Experiment 4 registration: reward mass and internal correspondence precision

Registered 2026-09-30 before generating/scoring the new synthetic evaluation. This is an engineering experiment with controlled truth, plus real-corpus development diagnostics. It does not evaluate generalization to additional FL source works or semantic decipherment.

## Fixed input sets

- Real development: all nine works from the final v3a benchmark, same documents, reference edges, and frozen v1 lexicon.
- Synthetic calibration: eight cases, seeds 4301–4308, one per family.
- Fresh synthetic denominator: 40 cases, seeds 4401–4440, five per family. Families: diagonal boundaries, source split, FL split, English insertion, English deletion, abbreviation split, sentence reordering, sparse anchors. No outcome-dependent replacement or parameter search.
- Each case is a generated substitution text with known token identities. Content words use artificial forms absent from the frozen v1 lexicon. The function forms for 'the' and 'and' agree by construction with eligible frozen v1 hypotheses; sparse-anchor cases omit them. This deliberately constructed domain is not evidence of natural-language translation accuracy.
- Each query has four opaque source candidates: one corresponding packet and three within-sentence word permutations. Correct candidate position is randomized per seed. The model receives only saved text and the original frozen lexicon, never token IDs, substitution keys, candidate answer, or reference edges.
- Synthetic edge and token truth comes from shared generated token identities, allowing explicit insertions, deletions, and non-monotonic sentence order. Raw synthetic text, token-span gold, split identity, seed, normalized documents, and hashes are frozen before execution.

## Four fixed variants

Cross reward mode (v3 effective-unit mass / token mass) with emitted edges (v3 Cartesian / ordered token path). All variants use protected abbreviations, up to 2:2 effective-unit blocks, the exact v3 lexical score blend, match floor 0.72, and frozen v1 eligibility rules. No register normalization or new lexicon induction.

Effective mode reproduces v3: reward = (similarity - 0.72) × mean effective-unit count - 0.04 × extra effective units; gap 0.35 per effective unit; strength divided by FL effective-unit count.

Token mode uses a 20-token reference mass. M = mean FL/source word-token count / 20. Reward = (similarity - 0.72) × M - 0.04 × max(0, M - 1). Gap cost = 0.35 × skipped-unit token count / 20. Strength is divided by total FL word-token count / 20. The identical token-span block has identical reward under regrouped boundaries; feasible block proposals still depend on the up-to-2:2 search limit, so globally identical retrieval is not guaranteed.

Ordered decoding is a separate postprocessing stage on selected blocks. Use a global monotonic token DP within each block: eligible frozen predicted word matching source token scores +2, known mismatch scores -2, unknown token diagonal scores 0.5 minus absolute difference in normalized token-center positions. Each token gap scores -0.75. Deterministic diagonal-first maximum. Retain diagonal pairs with nonnegative score. Emit an atomic sentence edge when at least two retained token pairs support it OR at least one is an exact frozen lexical match. Record token spans and anchor/positional basis. This is a provisional positional model, not validated semantics. Cartesian mode emits all block cross-product edges as before and has no token-pair claim.

The block search and rankings depend only on reward mode, not the edge decoder. Admission uses emitted edges, so decoding can cause additional abstention. Require at least three distinct FL atomic sentences with emitted edges, a unique top candidate (strength margin > 1e-9), and strength above the registered calibration rule.

## Calibration, evaluation, and controls

- Calibrate separate reward thresholds: maximum wrong-source strength on nine real development queries for the real panel, and on eight synthetic calibration cases for the synthetic panel, plus 1e-6. No fresh synthetic scores set thresholds. Edge variants share reward thresholds.
- Real panel: source ranking, conditional/end-to-end edge precision/recall, extra-edge counts, Misinfons and Christisis diagnostics. Treat all real results as development evidence.
- Fresh primary: uniquely correct top-1 / 40, correct admissions / 40, edge precision/recall including unadmitted top retrievals, source-absent false admissions / 40. Report all four variants and all eight families. Ordered variants additionally report token-pair precision/recall against generated identities.
- Source-absent control removes the corresponding candidate. Real controls remove every edition of the correct work.
- Twenty shared FL atom permutations per real query, seed 4731; recompute adjacent blocks. Synthetic fresh controls use ten shared FL atom permutations per case, seed 4831. Each decoder applies the same admission rule to each observed/absent result. Exceedances are descriptive, not p-values.
- Metamorphic diagnostics: for each real block with identical token spans feasible under legacy/protected units, compare its reward directly under both representations. Report raw reward differences for effective and token modes. These do not count as fresh source confirmations.
- Preserve all run states, hashes, reference spans, blocks, provisional token paths, inferred edges, predictions, rankings, candidate margins, calibration cases, and controls. One final execution after synthetic implementation tests. No winner selection, retry, or tuning after fresh outcomes.
