# Experiment 52: uniform scope adds nested paragraph text on three of five pages

The registered structural rule adds paragraph-channel text on **3 of 5 saved
publisher pages**. It leaves paragraph membership on the original v42 reference
page unchanged and excludes form text on every page. All **265 entry-content
text leaves** are accounted for with exact original parsed-body coordinates.
The engineering accounting criterion passes; no scaffold score was computed.

The stricter v51 identity diagnostic is false on all four v50 captures: each
Open Graph URL omits **/a/** while the canonical/final article URL includes it.
No alias was assumed or tested. Old dates, scopes, scores and readiness remain
fixed, including the v50 **1/4 ready** result and unmet four-ready capacity.

## Frozen cohort and structural rule

The [registration](../experiments/cohort_scope_v52.md), config, code/tests and
**112 input hashes** were frozen before computing new cohort scopes. All five
pages were retained: the original publisher reference and every v50 slot,
including both out-of-window pages and the missing-h1 case. The earlier v51
one-page audit is prior exposure, not erased or relabeled as an untouched test.
There were **zero network requests and zero browser renders**.

Each original body and old direct-paragraph extraction was reproduced exactly.
Every nonempty body text leaf was mapped in DOM order to the original joined
body, rather than located by a text search. Repeated strings therefore retain
distinct original positions. These spans are Unicode coordinates in parsed
body text, not raw HTML byte positions, browser geometry or historical evidence.

The same ancestor-priority rule labels every container leaf: **form, table,
figure, blockquote, list, heading, paragraph, other**. Higher-priority structure
wins even inside a direct p. Paragraph is a markup label, not certified prose,
language or semantic relevance. Caption, heading and form text stay in separate
ledgers rather than disappearing from the accounting.

Prospective paragraph runs join only adjacent leaves with the same paragraph
owner and one original body separator. A different owner, excluded leaf or body
gap ends the run. No new text is passed to an anchor extractor, and no identifier
can be manufactured by deleting intervening text. All p owners, including empty,
non-paragraph-channel and nested owners, remain in a separate inventory.

## Complete five-page comparison

| Page | Old direct p units | Old included leaves | New paragraph leaves | Added / removed leaves | New nonempty paragraph runs | Empty p owners |
|---|---:|---:|---:|---:|---:|---:|
| Reference v42 | 14 | 34 | 34 | 0 / 0 | 14 | 0 |
| q00s00: Glashow report | 11 | 24 | 24 | 0 / 0 | 11 | 0 |
| q00s01: Halzen report | 23 | 39 | 50 | 11 / 0 | 24 | 4 |
| q01s00: Askaryan Radio Array | 12 | 27 | 30 | 3 / 0 | 13 | 0 |
| q01s01: under-water report | 21 | 39 | 47 | 8 / 0 | 25 | 1 |
| **Total** | **81** | **163** | **185** | **22 / 0** | **87** | **5** |

Old unit counts include empty direct paragraphs; new runs are nonempty spans,
so these are different denominators. Empty-owner counts cover all descendant p
elements, including those outside the paragraph channel. There were **105 p
owners** in total and no owner containing another p in these five captures;
nested-p handling remains covered by a fixture.

All **22 added paragraph leaves** come from the three stated pages. No old
included leaf is removed in this observed cohort, but the rule does not assume
that outcome: a fixture verifies that higher-priority form text inside a direct
p is removed. On the reference page, selected leaf membership and its fourteen
paragraph runs reproduce the original paragraph scope; the old quotation masks
and numeric results were not recomputed or changed.

| Uniform channel | Text leaves across five pages |
|---|---:|
| Paragraph | 185 |
| Form | 45 |
| Figure / caption | 14 |
| Heading | 15 |
| List | 3 |
| Other | 3 |
| Table / blockquote | 0 |
| **Total** | **265** |

All pages retain **nine form leaves outside paragraph runs**. No source form
instruction was followed, and no form or script was submitted/executed. Full
container and legacy direct-p text are exactly reconstructed from their leaf
ledgers. Per-channel character counts, owner identities, added/removed indices
and every run's original span are saved in the local [scope ledgers](../data/v52/).
No count is presented as semantic coverage, accuracy or new independent evidence.

Reported character totals distinguish sums of run lengths from strings joined
across paragraph units. For example, the reference's 5923-character legacy join
has thirteen between-paragraph spaces beyond the 5910 characters summed over
its fourteen unchanged runs. This serialization difference is not content loss.

## Uniform identity diagnostics and unchanged intake

The sealed v51 title/identity diagnostic was applied without modification to all
five pages. Title strings agree in the inspected metadata families, but strict
URL agreement passes only for the reference page. All four v50 canonical URLs
match their nominee/final URL; each og:url has the same slug **without /a/**.
The missing-h1 page still has no h1. The other pages' h1 inventories are unchanged.

| Page | Strict metadata/URL diagnostic | Old v50 readiness |
|---|---|---|
| Reference v42 | True | Outside the v50 intake denominator |
| q00s00 | False: URL disagreement | False: date after cutoff |
| q00s01 | False: URL disagreement | False: date after cutoff |
| q01s00 | False: URL disagreement | True under the original v50 rule |
| q01s01 | False: URL disagreement | False: no h1 |

The original v50 identity check required at least one matching canonical/og:url
value; the stricter diagnostic requires both channel kinds and every value to
match. It does not retroactively revoke or promote readiness. Metadata fields
share one publisher response and are not independent corroboration. No request
to a stored alternate URL or redirect/alias inference occurred. The URL-path
disagreement remains unresolved across four captures.

## Verification, limits and next step

**398/398 full-workspace tests** and **359/359 isolated-public-export tests**
pass; the same 39 archive-dependent tests remain excluded publicly. Eight new
fixtures cover repeated text with distinct coordinates, inline/nested/empty p
owners, category priority, removal of old-included form text, no joining across
gaps or owners, nested-p ownership, Unicode spans/comment/script exclusion and
body/container identity failures.

The [separate verifier](../scripts/verify_cohort_scope_v52.py) reconstructs all
body-leaf positions, 265 container leaves, channels, owner inventories and runs
using a different traversal/grouping implementation. All nine accounting checks
pass on all five pages. The verifier checks all **51 prior manifests and
deliverable seals**, preserving old bodies, paragraph spans, date/title failures,
the v51 audit and readiness. See the [verification receipt](000052_verification.json)
and local [immutable report](../runs/000052_cohort_scope/report.json).

Both implementations share BeautifulSoup html.parser. Title diagnostics replay
the same sealed v51 helper; critical URL fields are checked separately. This is
same-agent engineering verification, not independent review, proof of browser
visibility or validation of semantic prose scope. Widgets outside form structures,
unwrapped narrative, captions and list/table content can require different
treatment in a future declared representation. Historical bytes and independent
source groups remain unresolved.

This step adds no scaffold/alignment, numeric/uppercase, opaque lexical or
semantic scores. No readiness, meanings, immediate source identities, independent
reviews or untouched natural units are admitted. The old intake remains 1/4,
both intake/natural-benchmark capacities remain unmet, and scientific acceptance
and semantic metrics stay null.

Next bounded step: preregister a **routing/provenance check of the four exact
stored og:url endpoints**, with one bounded native route per endpoint and no
new discovery. Preserve failures, redirect limits and all original captures;
compare observed final/canonical/title identity with the frozen records. This
can test current URL aliasing without assuming it, changing date/h1 decisions,
authenticating historical routing or claiming FL source identity. No such
request or new cohort scoring is part of this experiment.
