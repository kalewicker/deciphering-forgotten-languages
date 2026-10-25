# E92: a complete, source-linked annotation representation

The frozen adapter accounts for **86/86 candidate documents** and recognizes
**3,485 candidate line pairs**, matching every document's index-declared count.
All 86 documents have one internally consistent filename/number/title/locator
join to both index and source catalog. There are **zero unsupported blocks,
unresolved joins or count mismatches** under the declared rules.

This resolves the format bottleneck. It does not authenticate native FL text,
validate English meanings or establish independent source groups. The package is
an exposed third-party annotation resource, not a newly verified parallel corpus.

## Development and complete census

The [development protocol](../experiments/yid_adapter_v92.md) and input hashes were
registered before inspecting five fixed member prefixes: candidate numbers 01,
43 and 86, the index, and the source catalog. Each inspection was limited to the
first 8,000 Unicode code points. Candidate 01 was fully visible (5,594 characters);
the four other samples were partial. Exact exposures and full-member hashes stay
local. E91's previous whole-package machine inspection is not erased.

The sample established a two-line, blank-separated pair layout and explicit
filename fields in both catalogs. The adapter was developed on those examples
and synthetic edge cases, then [frozen](../experiments/yid_adapter_v92.json) before
one full census. No after-census parser changes or fallback occurred. Titles and
body units are not distinguished; pair counts are layout counts, not verified
sentence segmentation or aligned meaning.

All original line endings and content remain traceable through Unicode code-point
spans. Every candidate character belongs to a content block or separator. Catalog
prefixes, complete rows, source-claim spans, fields and literal URLs remain in the
local ledger. The combined edition contributes no units: E91 already established
that it contains the individual documents verbatim. All 180 ZIP entries retain
explicit dispositions; packaging remains opaque.

| Accounting result | Count |
|---|---:|
| Candidate documents / consistent joins | 86 / 86 |
| Index rows / source-catalog rows | 86 / 86 |
| Candidate pairs / declared-count mismatches | 3,485 / 0 |
| Unsupported blocks / unmatched catalog rows | 0 / 0 |
| Distinct joined native-shaped locator literals | 86 |
| Repeated locator classes | 0 |
| Source-claim records | 265 |
| Missing auxiliary files explicitly named in the index | 1 |

The named but absent auxiliary file is `YID-LEXICON.txt`. No recovery or download
was attempted. The 265 source-claim records are author-supplied bullet entries,
not 265 distinct works, independently verified sources or reviewed passages.
Identical native-shaped locators in two package catalogs establish internal
consistency only; no URL was fetched.

## Material limitation and next decision

The sampled index states that its Yid lines are normalized and that English
readings mix source-aligned wording, source-guided readings and contextual
reconstructions. It also states that the reading edition omits the evidence labels.
Consequently, even this fully resolved layout cannot supply per-unit truth labels
or raw native-text provenance. Source-catalog prose is preserved as claims; no
unit-level confidence or evidence category was inferred from it.

**Representation is now usable for a bounded corroboration task, not modeling.**
The next justified step is to register a small deterministic native-text comparison
sample and an explicitly bounded feasible acquisition route before fetching any
listed post. Compare the package's candidate first lines with saved native text,
retaining normalization differences and failures rather than silently repairing
or selecting favorable material. Do not retry the stopped TLS/archive/pagination
routes merely because this package supplies URLs. If no feasible new route exists,
record the resource barrier and stop before a confirmation panel.

Only subsequent native-text corroboration and source-group capacity assessment
could justify reserved evaluation material. English renderings remain hypotheses;
semantic validation still requires independent evidence/review. Yid is a different
development resource, not same-language confirmation of E79's Kamri result. The
natural semantic benchmark remains **0/4 qualifying works**.

No network requests, models, predictions, source adjudication, language verification,
lexicon induction, semantic review or corpus admission occurred. E92 ends here.

## Verification

A separate read-only verifier imports no production adapter. It reconstructs
physical lines and partitions, catalog fields/claims, literal joins, failure
reasons and all summary counts; verifies input/output hashes; and accounts for
all 180 entries. Both implementations share standard-library ZIP/regex behavior
and the written layout specification. This is computational checking, not an
independent reviewer or source-authentication result.

**662 workspace tests and 623 isolated-public tests passed**, with the established
39 archive-dependent exclusions. Nine new fixtures cover Unicode and CRLF spans,
invalid block lengths, Unicode non-LF separators, exact joins, repeated fields/rows,
conflicting locators/counts, unmatched catalog rows, duplicate representations,
missing auxiliary files and empty documents. All five saved development exposures
were checked against archive bytes; all twelve E91 sealed artifacts remain unchanged
and match the preceding local evidence checkpoint.

Public files contain the adapter, protocols, tests, aggregate report and receipts.
Document text, locators, source claims, unit ledgers and development excerpts remain
local-only. Read-only replay requires the local archive:

```sh
.venv/bin/python scripts/verify_yid_adapter_v92.py
```

The freeze and run commands refuse to overwrite their registrations/run directory.
