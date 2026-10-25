# E86: one native Older Posts target identified

The offline pagination inventory identifies **one unambiguous older-listing URL**
in the user's saved Chrome page. Both primary and independent implementations
agree on its exact href and selection. No page was fetched and no predictions
ran. This is a navigation/resource result, not new confirmation material.

The [protocol](../experiments/listing_navigation_v86.md), code and
[registration](../experiments/listing_navigation_v86.json) were frozen before
navigation inspection. E85's snapshot and all sealed evidence remain unchanged.
E85's **0/4 new nominations** remain preserved; this result does not replace them.

## Full fixed-scope inventory

The union of pager anchors, explicit older signals and rel=next anchors/head links
contains exactly two tags:

| Global DOM tag index | Label | Metadata | Disposition |
|---|---|---|---|
| 748 | Older Posts | id Blog1_blog-pager-older-link; class blog-pager-older-link | Valid explicit older route |
| 749 | Home | class home-link | Not a native Kamri pagination URL |

There is one older signal and one distinct eligible older href. No base href or
conflicting eligible rel=next route is present. The explicit older class supplies
direction; the differently prefixed DOM id is recorded without being invented as
a separate exact-id signal. Other article links and prose were outside this scope.

## Sole next capture target

[Open the exact Older Posts listing](https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri?updated-max=2022-11-30T07:37:00%2B01:00&max-results=20&start=1&by-date=false)

```text
https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri?updated-max=2022-11-30T07:37:00%2B01:00&max-results=20&start=1&by-date=false
```

This is the HTML parser's decoded href, with original query encoding/order
preserved. It was not generated from the known article's date. The query contains
an updated-max cursor, max-results=20, start=1 and by-date=false. It requests up to
20 results; neither the actual returned count, URL novelty, connected-work
independence nor useful text capacity has been tested.

The metadata indicates a native route to try through the user-mediated browser
resource. It does not establish that it currently resolves or returns the same
content. No DNS, HTTP, browser, asset or archive request was made by E86.

## User-assisted capture handoff

Save **this exact page only** with Chrome's page-save function, retaining the HTML
and any companion folder unchanged. Supply their paths and the requested/final
address-bar URL, browser/save method, full save date/time with AM/PM and time-zone
label if known. Do not infer unavailable facts or select favorite posts first.
A user-supplied capture will be preserved and separately registered before link
selection or modeling. Its expected origin is this query-bearing route; do not
silently strip the pagination parameters to force an origin match.

This freezes one next resource target, not a multi-page collection or model
campaign. If that page fails to open or save, preserve the failure rather than
substituting another cursor. Future parser scope, representation and provenance
decisions belong to a new intake protocol. No automatic next-page iteration or
post fetch is launched here.

## Boundaries and verification

All earlier acquisition failures, E82's rejected listing, E84's restricted-WARC
barrier and E79's adaptive development pass remain intact. No new independent
group, source identity, meaning, review or untouched unit is admitted. The separate
semantic benchmark remains **0/4 qualifying works**. Eligibility of new material
remains unresolved until it is actually supplied and assessed.

The verifier imports no E86 production functions. It reconstructs global DOM
indices and pager scope using tree ancestry, independently checks URL/query
conditions, retains both tags and reproduces the unambiguous selection. Shared
BeautifulSoup and standard URL/date parsing are disclosed. Agreement is accounting
verification, not independent capture authentication or scientific review.

Six fixtures cover older-link absence/ambiguity, duplicate agreement, URL/query
limits, rel=next conflict, base rejection and irrelevant-link exclusion.
**621 workspace tests and 582 isolated-public tests pass**, with the same 39
archive-dependent exclusions. Raw metadata ledger remains local; public main
contains code, protocol and this small handoff report.

Read-only reconstruction requires the local archive:

```sh
.venv/bin/python scripts/verify_listing_navigation_v86.py
```

Preparation and execution are single-use; do not overwrite sealed paths.
