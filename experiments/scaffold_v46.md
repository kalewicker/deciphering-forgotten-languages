# Experiment 46: literal masked-residual scaffold with order controls

Question: after removing known English quotations/title/bibliography, does the
target's ordered numeric scaffold separate from fixed bag-preserving order controls
of the publisher material? This exposed development assay cannot establish word
meanings, quantity equivalence, ancestry, immediate source identity or significance.
The earlier near-copy/parent-absent failures and all quotation results remain fixed.

Freeze original target, eight quote spans, raw publisher HTML/body, v45 context,
all 45 old manifests/seals, code/tests/config before anchor extraction or scoring.
Only structural HTML scope/boundary inspection precedes registration; no anchor
inventory or score informs scope selection. Zero network requests. One source
re-extraction must exactly reproduce v42's body.

Target masks: [0, start of quote00), all eight original English content spans,
and the bibliography from the unique literal marker in JSON through target end.
Validate every quote against original target and marker at frozen offset 7332.
Retain all complement intervals, including ones with no anchors; this is known-
English-masked residual text, not independently certified opaque-language scope.

Source scope, selected from markup before measurement: the 14 direct p children
of the unique `article#post-72762 > div.entry-content`. Exclude nested forms,
cards, sidebars and header/footer by this structural rule, not by anchor contents.
Each nonempty p must map uniquely to v42's body, or the audit stops unavailable.
Mask every balanced curly-double/ASCII-double quoted span within each p, using
the declared parser. Unbalanced/nested unsupported quotation scope stops the run.
Preserve all original paragraph spans/text and masks locally.

Scan original text, not space-edited text. Numeric-looking candidates follow
`[0-9]+(?:[.,][0-9]+)*`; uppercase-Latin candidates follow `[A-Z]{2,}`. Reject
any candidate adjacent to a Unicode alphanumeric/underscore, and reject numeric
candidates preceded by dot/comma (unsupported leading-decimal boundary). A
candidate must lie wholly in a retained scope and overlap no mask. No partial
identifier rescue, quantity/unit parsing, date/range merging, acronym expansion,
case/decimal normalization or selected anchor list. Preserve exact spelling:
100.000 differs from 100,000. Key is candidate kind plus literal surface string.

Keep every occurrence with original character span, scope unit and index. Compute
numeric-only, uppercase-only and combined counts, shared distinct keys, multiset
overlap capacity and longest common subsequence (LCS) length. Report lengths
only, never a selected alignment/point ancestry path through repeated anchors.

Order controls preserve the complete source-anchor bag: global reversal,
within-paragraph reversal, 16 global-anchor permutations and 16 paragraph-block
permutations keeping within-paragraph order. SHA-256 index ordering with the fixed
JSON seed and exact family/draw/index strings makes all draws reproducible.
Retain identity, duplicate and tied draws without replacements. Keep zero-anchor
paragraphs in block permutations. There are 34 controls; report every score,
per-family maxima and tie/greater counts. No p-values or calibration are inferred.

Functional checks: every emitted anchor avoids masks; both target/source self-copy
scores equal their counts; all 34 controls preserve exact bag and index inventory.
The registered descriptive separation gate is eligible only with at least three
distinct shared numeric keys and passing functional checks. It passes only if
observed numeric LCS strictly exceeds every control in every family; ties fail.
Otherwise record false (eligible but unseparated) or null (sparse/invalid). Report
all uppercase/combined diagnostics without promoting them to a substitute gate.

Test mask leakage, literal number distinctions, identifier boundaries, repeats,
bag preservation/duplicate retention, structural scope ambiguity and LCS against
small exhaustive subsequences. Separately verify extraction, every mask/anchor,
all permutations and LCS via a full dynamic program; check all 45 previous runs
and seals. No threshold, normalization, seed or scope changes after scoring.

This is one opaque-residual structural assay, zero opaque semantic/lexical scores.
No source identity, meanings, independent review or untouched test units admitted;
scientific acceptance and semantic metrics stay null even if order controls pass.
Same-topic/near-copy alternative source documents are not tested by these controls.
Seal evidence/report, run full/public checks, checkpoint locally, commit/push main.
