# Experiment 67: author-format correction passes; versioned development PDF frozen

The new author-format policy passes **7/7 metadata checks** against E66's exact
saved response. The native literal `Weinstein, Steven` parses to given component
`steven`, family `weinstein`, with its comma-order form retained. The complete
E66 assessment replays exactly, including its **false** gate and six passing
non-author checks. E66's historical result and skipped PDF stage are unchanged.
This is an explicitly post-failure development correction, not blind validation.

One new request to the fixed [arXiv v1 PDF](https://arxiv.org/pdf/0812.0349v1)
completed **HTTP200**, with zero redirects. The saved PDF has **15 pages** and
**481,674 bytes**. Both parsers agree on page count. All **5/5 first-page machine
checks pass**, and direct inspection of the entire first-page rendering confirms
the title **Nonlocality without nonlocality**, author **Steven Weinstein**, and
left-margin marker **arXiv:0812.0349v1 [quant-ph] 1 Dec 2008**. All three visual
identity fields are recorded as pass. The full PDF is now frozen locally as
version-addressed development material.

## Acquisition and identity accounting

| Item | Result |
| --- | --- |
| Source slot / selected identifier | 1 / arxiv:0812.0349 |
| Corrected metadata checks | 7/7 pass |
| Preserved E66 gate | False; original 6/7 unchanged |
| Six non-author metadata criteria | Unchanged and passing |
| New metadata / discovery requests | 0 / 0 |
| New route / application responses | 1 / 1, within fixed 1 / 1 budget |
| Redirects / retries / replacement sources | 0 / 0 / 0 |
| Saved PDF / two-parser page counts | 481,674 bytes / 15 and 15 |
| First-page machine identity checks | 5/5 pass |
| Visual title / author / version fields | Pass / pass / pass |
| Pages text-extracted and visually inspected | Page 1 only |
| Full-paper visual review | Not performed |
| Version specified by the FL citation | Unspecified |
| Edition chosen prospectively for development | v1 |

The PDF SHA-256 is
`af145b65dd7f89a92dcb685ffd6eae0fc818cda2a38dc3a0631be16d2b84d1bc`.
The native metadata history already captured in E66 lists v1 at
2008-12-01 19:46:58 UTC. The rendered first page's date agrees at day resolution.
These are provider/document observations, not independent authentication that
these bytes existed unchanged in 2008, or that the FL author used this edition.
No additional metadata or version-history request was made.

## Scope of the correction

The new grammar accepts one author in `given family` or `family, given` form,
retaining the original literal and parsed components. It rejects malformed,
unsupported or explicitly ambiguous lists/suffixes rather than inventing names.
It is deliberately limited to Latin tokens and a single family token. In an
unmarked name the last token is treated as family; surname particles and global
personal-name conventions are not resolved. The abbreviated citation establishes
only compatibility with family Weinstein and first initial S.

The PDF check also uses parsed metadata components, so the native comma-order
string need not occur verbatim in a normally ordered PDF byline. It requires the
complete metadata given components and family in one of the two fixed contiguous
forms, with word boundaries. It does not accept a longer surname substring,
initial expansion, arbitrary word permutation or fuzzy spelling. The author
witness is `steven weinstein` at normalized first-page span **[33, 49)**;
these are explicitly normalized coordinates, not original page-text offsets.

All transport, page-count, title and exact version-marker criteria are retained.
The first page was rendered in full and inspected, including the rotated version
marker. Its abstract/introduction were visible during that inspection, so the
page is exposed development material. No opaque FL text or English passage was
compared against it, and the remaining pages were not text-extracted or visually
reviewed in this experiment.

## Verification and scientific boundary

Ten new adversarial fixtures pass. **511 full-workspace tests** and **472
isolated-public snapshot tests** pass; the same **39** archive-dependent cases
are explicitly excluded publicly. The separate verifier imports no production
E67 functions. It independently reconstructs the observed author parse and all
old/new metadata checks, confirms the old false gate, replays selection, limits,
receipt timing and curl telemetry, re-extracts first-page text, and reproduces
exactly the saved PNG bytes from the PDF. It checks every output file and all
**66 previous run manifests and historical deliverable seals**.

Shared components are BeautifulSoup, the old URL exposure recognizer/header
replay, pypdf and pypdfium2. The visual receipt is bound to the image and PDF
hashes; same-agent replay cannot independently validate that visual judgment.
See [verification](000067_verification.json). Raw PDF, capture response/headers,
metadata derivative, rendered first page and visual receipt remain local in
`data/v67/`; run artifacts are in `runs/000067_author_format`.

A cited versioned document is available for a next controlled test. Its immediate
relationship to opaque FL passages remains **untested**. No lexical/alignment
scores, source-identity/meaning admissions, new confirmed connected-work groups,
independent reviews or untouched test units are added. The incomplete frozen
76-URL registry cannot establish independence, and E65/E66/E67 material is exposed.
Natural-benchmark capacity remains unmet. E63's original gate remains false,
E64's restricted metadata view is unchanged, and E62's ANITA route stays closed.

**Next:** register one bounded passage-presence screen over this fixed post/PDF
pair. Freeze the complete pre-reference prose-block inventory, full-PDF text
extraction rules, literal matching/normalization and positive/negative controls
before computing any matches. Retain every block and zero-match result. Exact
English presence, if found, would support only that literal observation; it
would not establish opaque meanings, whole-post source identity or an untouched
benchmark. This acquisition/identity milestone is complete.
