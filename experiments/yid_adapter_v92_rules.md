# E92 developed rules, frozen before the complete census

Development inspected only the recorded first 8,000 code points of candidates
01, 43, 86 and the index/catalog. Candidate 01 fits entirely in that window;
other sampled members extend beyond it. The exact exposure receipt is local.
No additional examples were selected. E91 had already machine-scanned all files.

Candidate layout: LF-delimited physical lines, with optional terminal CR removed
only from the content span. No Unicode normalization, decoding substitutions or
language detection. Blank lines contain only spaces/tabs after CR removal.
Consecutive nonblank lines form a block; exactly two lines make a candidate pair,
first declared Yid, second declared English. Every other block is unsupported.
Separators, prefixes, malformed content and original line-ending spans remain
accounted for. Titles are not distinguished from prose. Semantic validity is not
inferred from line order. No joining wrapped lines or splitting sentence clauses.

Auxiliary rows begin with a line consisting of decimal integer, period, space and
nonempty title. A row ends at the next marker or EOF. Preserve the entire prefix
and all row spans. Parse literal ASCII colon fields without case normalization.
Source claims start at column-zero '- ' bullets within source rows; preserve the
entire claim, citation span, fields and all literal HTTP(S) URLs. Claims may concern
multiple units, headings or contextual readings. Do not infer unit-level evidence
labels from those claims.

Join candidates by exact filename to index 'File' and catalog 'Translation file'.
Require exactly one matching row and one filename field in each, matching integer
numbers, matching catalog titles, one native-shaped original locator in each and
literal equality of those locators. Native-shaped syntax uses E91's unchanged
validator. Compare the index's single integer 'Sentence pairs' field with parsed
candidate pairs. Missing source claims, empty documents and unsupported blocks
are unresolved. Report every failure, unmatched catalog row and repeated locator;
no title similarity, URL cleanup, inferred filename or favorable-row selection.
A resolved join is internal annotation consistency, not source authentication.

Report source-claim record counts and any missing auxiliary .txt filenames listed
in index bullets. The sampled index says normalization was applied by its author
and evidence labels omitted; these annotation lines are not raw native text.
The index also mentions a lexicon; the census will report whether it is actually
present, without fetching it. Combined copies contribute no candidate pairs.

Freeze code, fixture tests, verifier, development receipt and prior input hashes
before one full census. Full-census failures remain recorded without repair.
Stop before native corroboration, source grouping, semantic review or prediction.
