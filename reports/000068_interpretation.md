# Experiment 68: no registered literal passage bridge in the cited v1 paper

The complete registered screen is negative: **0/16 whole target blocks** and
**0/1,000 consecutive 12-token queries** occur in the extracted text of the fixed
arxiv:0812.0349v1 PDF. There are zero target-hit occurrences. **15/15 positive
controls and 15/15 engineered negative controls pass**, with no marker collision.
The representation and visual gates pass. No query, target block, failed gate,
PDF edition or denominator was replaced after seeing the result.

This is evidence about the registered literal representation. It supplies no
literal passage bridge for this pair under these rules. It does not establish
that the citation is wrong, that the post has no relationship to the paper, or
that an opaque transformation, paraphrase, shorter overlap or different edition
is absent. The citation itself did not specify an edition; v1 remains a
prospective development choice. No translation or immediate-source claim follows.

## Complete accounting

| Item | Result |
| --- | ---: |
| Fixed post/PDF pairs | 1 |
| E65 nonempty owner runs accounted for | 48 |
| Included pre-reference structural prose blocks | 16 |
| Excluded title/copyright/non-prose runs | 3 |
| Excluded reference-tail runs | 29 |
| Whole-block queries present / denominator | 0 / 16 |
| Twelve-token queries present / denominator | 0 / 1,000 |
| Target blocks with fewer than 12 tokens | 0 |
| Target-hit occurrences / source hit pages | 0 / 0 |
| PDF pages extracted / fixed page denominator | 15 / 15 |
| Source Unicode characters, including 14 page separators | 38,001 |
| Source whitespace tokens | 6,333 |
| Positive controls passed / denominator | 15 / 15 |
| Engineered negative controls passed / denominator | 15 / 15 |
| New network or discovery requests | 0 |
| Source pages rendered and visually inspected | 1 and 15 |

Every nonempty direct div[align=justify] owner run before E65's fixed reference
boundary is included. No language, quotation, topic or apparent relevance filter
was applied. All repeated text and overlapping queries retain their own original
body/token coordinates. The scope ledger preserves the three pre-reference
non-prose owners and all 29 excluded reference-tail owners. All 16 target blocks
have a whole-block query, including the opaque-looking blocks; none are treated
as established translations or independently validated language units.

Each PDF page is the unmodified pypdf extraction from E67's frozen PDF, with
headers, footers, references, footnotes and line-break hyphens retained. The
first page exactly agrees with E67's extraction; pypdf and pypdfium2 both report
15 pages. Page strings are joined with one newline and every source token maps
to page-local and document coordinates. Cross-page matches were allowed by the
sequence search while intervening header/footer tokens remained present.

Matching uses exact contiguous whitespace-token sequences after NFC and
casefold. Punctuation and hyphenation remain literal. No additional typographic
repair, dehyphenation, fuzzy spelling, shorter-window search or paraphrase test
was performed. Zero matches therefore cannot be generalized to a normalized,
reflowed or otherwise transformed source representation. Every target query and
its empty match list is preserved, rather than only a selected summary.

## Controls, visual scope and verification

Each page's first 12 tokens supplies its own positive query, searched against the
whole document with its original prefix occurrence required. Each negative is
that prefix plus the fixed absence marker and is searched over the whole source.
These are engineered pipeline checks; they do not measure real absent-source
specificity or a false-positive rate. All 30 control rows and any duplicate
occurrences remain in the ledger.

The registered first/last pages were rendered and inspected in full; there were
no additional target-hit pages to render. Both images are legible. Page 1 shows
the previously audited title/byline/version, and page 15 contains bibliography
entries with visible line-break hyphens and typographic ligatures. Pages 2-14
were text-extracted and searched but not visually reviewed. Whole-paper
extraction fidelity is not established by these two checks. The entire pair is
exposed development material, not an untouched benchmark.

Ten new adversarial fixtures pass. **521 full-workspace tests** and **482 isolated-
public snapshot tests** pass; the same **39** archive-dependent cases are excluded
publicly. The separate verifier imports no production E68 functions. It rebuilds
the target DOM scope, all source page/token coordinates and every target/control
query, then verifies all **1,046 query rows** with normalized-string search and
token-boundary tables instead of the production 12-gram index. It reproduces the
complete empty target match lists, all positive/negative control occurrences,
and exact saved render bytes. It checks every output file and preserves all
**67 earlier run manifests and historical deliverable seals**. See
[verification](000068_verification.json).

Shared components are BeautifulSoup, Unicode NFC/casefold, pypdf and pypdfium2.
The visual receipt is hash-bound to the PDF/images; same-agent replay cannot
independently verify the visual judgment. No independent scientific review is
claimed. E66's original false metadata result, E63's false original gate and
E62's closed ANITA route remain unchanged.

Raw/derived text, all query/hit/control tables and images stay local in
`data/v68/`; the run is `runs/000068_passage_presence`. There are zero new meaning
or source-identity admissions, confirmed independent connected-work groups,
independent reviews or untouched test units. Natural-benchmark capacity is unmet.

## Next boundary

This registered literal screen is complete. Do not lower 12, drop punctuation,
change editions or try another citation merely to obtain a match. The useful
next step is a separately registered, tightly bounded **quotation-attribution
pilot** using one already exposed English block from this post with a fixed
selection rule and search budget. That asks for evidence tied to actual wording;
the fact that a cited work is easy to dereference has now proved insufficient
for a literal bridge in this pair. Preserve E68's negative result and require a
frozen candidate/edition and controls before any later passage test. No such
search or new source acquisition occurred in E68.
