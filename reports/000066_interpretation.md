# Experiment 66: arXiv record captured; fixed author-order parser blocks the PDF stage

The single registered metadata request completed **HTTP200**, with no redirect.
The record at [arXiv 0812.0349v1](https://arxiv.org/abs/0812.0349v1) reports the
expected title, **Nonlocality without nonlocality**, and author metadata
**`Weinstein, Steven`**. Its submission history lists v1 at **2008-12-01
19:46:58 UTC** and v2 at **2008-12-03 00:57:17 UTC**. These are claims in the
captured native record, not independent historical corroboration.

The frozen metadata gate passes **6/7 checks** and fails
`single_compatible_author`. **This is an implementation limitation:** the author
parser assumes given-name-first words, with family name last and first initial
first. The provider returns family-name-first comma notation. The recorded
failure does not establish a different author or a wrong cited work. The
aggregate run status `metadata_mismatch` means the fixed gate failed; its precise
cause is author-order parsing, not observed personal-identity disagreement.

The conditional PDF request was correctly **skipped**. No PDF or versioned
source bytes were frozen, and no page was extracted, rendered or visually
reviewed. There was no retry, replacement candidate, alternate version, title
search, redirect, or use of the unused request allowance. The source slot stays
in the denominator as unavailable under this implementation. No historical gate
or post-acquisition criterion was changed.

## Registered accounting

| Item | Result |
| --- | --- |
| Source slot / selected source | 1 / arxiv:0812.0349 |
| Selection | First recognized arXiv identifier in E65 reference-tail order; row 27 |
| Version specified by the FL citation | None |
| Prospective edition policy | v1, conditional on native checks |
| Request / application response budget | At most 2 / 2 |
| Requests / application responses observed | 1 / 1 |
| Redirects / retries / new discovery requests | 0 / 0 / 0 |
| Complete exact native HTML | Pass |
| Single normalized title match | Pass |
| Single compatible author under frozen word-order parser | Fail |
| Native identifier match | Pass |
| Complete consistent native version-history rows | Pass; 2 rows |
| Native v1 year and before-post cutoff | Pass |
| Citation date in displayed cited year | Pass; 2008/12/01 |
| Conditional PDF request | Skipped because metadata gate failed |
| Version-addressed development PDF available | False |

The citation's unspecified version remains unspecified. Selecting v1 for a
prospective development capture does not show which edition the FL author used.
The live record does not authenticate publication-year FL wording or the opaque
post's relationship to this paper. The source ID was absent from the frozen
76-URL exposure inventory, which is incomplete; this absence provides no claim
of a newly independent connected work or untouched evaluation status. The
citation was already exposed in E65 and is development material.

## Verification and improvement

All **501 full-workspace tests** and **462 isolated-public snapshot tests** pass;
the same **39** archive-dependent cases are explicitly excluded publicly. The
nine new fixtures cover title/author/identifier mismatch, history completeness,
invalid dates/weekday/version order, version stripping/redirect refusal,
conditional first-page identity criteria, and fixed reference-order selection.
They did **not** cover valid family-name-first author metadata. Their success
therefore does not establish that the author parser handles native name formats.

The separate verifier imports no production E66 gate functions. It replays
selection, the exact curl command and zero-redirect/no-retry limits, raw response
hashes and telemetry, intent/receipt timing, all native metadata/history fields,
the six passing checks, the specific author-parser failure, skipped PDF stage,
complete output accounting and the unchanged **65 previous run manifests and
historical seals**. It shares BeautifulSoup, the old exposure recognizer and a
sealed header replay helper. Same-agent replay is engineering verification,
not independent review. See [verification](000066_verification.json).

Raw response, headers, telemetry, selection, exposure and assessments remain
local in `data/v66/`; the completed run is `runs/000066_arxiv_feasibility`.
E63's original gate remains false, E64's restricted metadata view is unchanged,
and E62's ANITA route remains closed. There are zero passage comparisons,
lexical/alignment scores, source-identity/meaning admissions, new confirmed
connected works, independent reviews or untouched test units. Natural-benchmark
capacity remains unmet.

**Next:** register an explicit author-name parsing correction in new versioned
code, accepting both `given family` and `family, given` forms with ambiguity
rejection and adversarial fixtures. Reuse these exact saved metadata bytes and
retain E66's failure. Bundle that offline repair with at most one conditional
request for the already fixed v1 PDF and its first-page version/title/author
audit. No new metadata request, source discovery or HTML identity-policy change
is needed to address this format issue. Stop on any remaining mismatch rather
than moving to a different source or relaxing the edition requirement.
