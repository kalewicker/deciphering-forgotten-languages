# E98: paginated HTML acquired; extraction failed before wording comparison

The catalog-selected HTML representation was retrieved successfully: **HTTP 200,
699,009 bytes**, strict UTF-8. It contains a coherent sequence of **351 numeric
page anchors**, including unique anchors 252–257 with matching printed labels.
Its header identifies the expected work, editor and 1898 imprint. This resolves
the immediate resource problem that blocked E97's plain-text representation.

However, the frozen extractor **failed before any target wording was compared**.
It required every parsed `.pagenum` element to contain exactly one numeric anchor.
The parsed document contains four such elements with two anchors each. The first
is associated with pages 2 and 3, outside the intended comparison windows. This is
an implementation limitation, not contrary wording evidence or absent pagination.
All 22 targets remain fixed; wording counts are **null**, not zero.

## Acquisition and disclosed procedural amendment

The [protocol](../experiments/burton_paginated_v98.md) fixed the existing Gutenberg
catalog entry and its first Read Online HTML link, plus one native HTML GET.
One provider catalog OPEN returned the Read Online link as opaque link ID 0 without
its destination URL. Before following it, a separate
[prospective addendum](../experiments/burton_paginated_v98_link_resolution.md) allowed
one provider CLICK solely to resolve that selected link. The original protocol
remains unchanged. The timestamped intent binds the addendum before the CLICK.

Thus the actual budget used was **two provider calls and one native GET**.
Internal provider HTTP transactions are unknown. The complete returned provider
texts remain local; incidental header/preface text exposure is disclosed. Provider
text was not used as raw DOM evidence or searched for the target renderings.

The selected URL was the catalog's same-ID HTML representation ending in
`/cache/epub/57208/pg57208-images.html`. System curl obtained it once with standard
certificate verification, no redirects, a 60-second maximum and 8 MiB limit.
No retry, TLS bypass, alternate edition or mirror was attempted. E96's text request
was not repeated or repaired. Intent, headers, bytes and receipt remain preserved.

The source is linked from the [Gutenberg catalog](https://www.gutenberg.org/ebooks/57208)
and represented by its [Read Online HTML](https://www.gutenberg.org/cache/epub/57208/pg57208-images.html).
Header compatibility does not independently authenticate the historical edition.

## What passed and what failed

Before target matching, a metadata-only inspection recorded all numeric page
anchors and the required printed labels. The six required anchors are unique,
ascending and locally labeled `[Pg 252]` through `[Pg 257]`. The global numeric
anchor sequence is 1..351. Header metadata agrees with the previously supplied
text. Exact metadata and inspection records are local.

The extractor and six synthetic fixtures were then frozen in a separate
[execution registration](../experiments/burton_paginated_v98_execution.json).
One execution reached the extractor's multiple-anchor assertion and stopped;
the run manifest remains `failed` with `AssertionError()`. No comparison artifact
was produced, and no literal or whitespace target search ran. The target list was
loaded as input but not scored. The earlier metadata evidence does not imply the
complete extracted-window gate passed.

Read-only structural verification identifies these multi-anchor parsed elements:

| First numeric anchor | Last numeric anchor | Anchors in element |
|---|---|---:|
| Page 2 | Page 3 | 2 |
| Page 130 | Page 131 | 2 |
| Page 286 | Page 287 | 2 |
| Page 288 | Page 289 | 2 |

This describes BeautifulSoup/html.parser's parsed structure. It does not diagnose
which raw HTML feature caused the nesting, and no parser/HTML repair was attempted.
The extractor was too restrictive for the real representation. Passing synthetic
fixtures did not establish compatibility with this document. Prioritizing only
well-formed page-label examples in those fixtures was an implementation weakness.

## Stop and next bounded correction

E98 is complete as a failed extraction attempt, with the successful acquisition
and metadata evidence preserved separately. Do not rerun or edit its frozen code.
No new download is needed to address the remaining obstacle.

The next useful step is a separately registered versioned extraction correction
on these saved bytes. It should establish a robust association between each page
anchor and its own printed label, retain neighboring prose even when parser nesting
is unusual, and exercise the observed structure in development fixtures before
freezing. Confirm the two exact page windows independently before running the
unchanged 22-target wording test once. Preserve all E98 evidence and prohibit
selection based on eventual target matches. No additional resource search is needed.

That correction is not launched here. Source wording, opaque meanings, translation
accuracy and unique source identity remain unresolved. Semantic capacity stays
0/4; no new untouched confirmation units or model results were admitted.

## Verification and publication

Read-only verification imports no production extractor. It checks acquisition and
execution hashes, timing, response size/status, the complete numeric anchor
sequence, required labels, unsupported structures and the absence of comparison
output. It shares BeautifulSoup/html.parser; it is not independent scholarly review.
E97 sealed artifacts remain unchanged and match the preceding local checkpoint.

**681 workspace tests and 642 isolated-public tests passed**, with the established
39 archive-dependent exclusions. Six new fixtures cover page-label removal, inline
adjacency, mismatched labels, separate-window boundaries, order/duplicate handling,
hidden elements and absence of spelling repair. These fixture results do not
supersede the failed real-document execution. No code was altered after failure.

Raw HTML, provider responses, exact locators, metadata and targets remain local-only.
Public main contains protocols, code, tests and aggregate findings. Replay:

```sh
.venv/bin/python scripts/verify_burton_paginated_v98.py
```
