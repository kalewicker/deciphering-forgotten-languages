# E95: offline source-claim audit for the three corroborated examples

Before opening the selected catalog entries for this audit, bind the saved E90
ZIP, E92 parsed catalog, E93/E94 corroboration results and this protocol by hash.
Fixed candidates: 01, 43, 86, all their source-catalog rows and every source bullet.
No selecting claims by apparent strength. This is descriptive inspection of author
claims, not independent review. Candidate 01's catalog prefix was previously seen
in E92; all entries were machine-parsed then. Nothing is claimed untouched.

Use E92's exact row and claim spans against strict UTF-8 SOURCES.txt. Preserve
selected rows and every citation, URL and Role field with character spans locally.
Verify raw member hashes against E90/E92. No network, source-document fetch,
new HTML inspection, rendering, model run or lexicon induction.

For each claim record, manually assess only what the catalog actually specifies:
(1) cited item and literal locator present; (2) claimed relationship (exact wording,
source-guided/contextual, reconstruction, or unspecified, allowing mixed claims);
(3) coverage scope as stated, including unit IDs/ranges/counts if present;
(4) source-side passage locator such as printed pages or named section;
(5) whether the entry itself supplies an explicit mapping from package pair ordinals
to source passage spans. Record evidence spans for each assessment; absence means
not supplied in this entry, not absent from the author's other research artifacts.
Do not convert ranges of external IDs or a count into a verified ordinal mapping.
Do not infer independence or semantics from a URL, a claimed lock or fluent English.

Account for every selected post and bullet, preserving ambiguous/mixed coverage.
Report which claims could motivate a concrete later wording test, separating
source accessibility (untried), claim specificity, ordinal alignment and independent
semantic validity. Recommend at most one next bounded falsification task based on
explicit passage specificity and feasibility leads, never a source verification
result. Preserve contrary/uncertain claims. If no adequately specified test exists,
state the missing mapping or source representation rather than fetching broadly.

Stop after audit, exact-span verification and aggregate interpretation. No threshold
for semantic admission, no corpus expansion and no changes to sealed historical
results. Public main receives code/protocol/aggregate findings; full catalog text,
URLs and evidence-span ledgers remain local-only. Semantic capacity remains 0/4.
