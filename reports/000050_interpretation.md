# Experiment 50: one ready publisher candidate; four-slot capacity unmet

The bounded intake captured all four nominated pages, but only **1 of 4**
passes the frozen capture/scope checks. The ready candidate is the publisher's
2014 Askaryan Radio Array article. Two other nominees have publication metadata
after the date cutoff; the fourth has **no h1 heading**, failing the registered
title rule. The four-ready-candidate planning criterion **fails**. No nominee
was substituted, no rule relaxed and no new candidate was scored.

## Registered discovery and selection

The [registration](../experiments/publisher_intake_v50.md), code/tests, config,
bounded prior-URL snapshot and **93 input hashes** were frozen before searching.
Exactly **two sequential search-tool calls** used the fixed Physics World
queries, with after/before operators for 2000-01-01 through 2018-09-30. The
visible responses contained **15 and 16 attributable result blocks**. Every
header, URL, result-block span/hash, topical check, duplicate/exclusion reason
and slot decision is preserved locally in the
[selection ledger](../data/v50/selection.json).

Eligibility used exact native article URLs and whole-word neutrino/neutrinos
plus ANITA/Antarctic/Antarctica in each returned title/result block. First
appearances across queries were retained, excluding the already captured v42
article and duplicate identities. The first two eligible hits per query filled
all four slots. Later hits and duplicate results were not discarded from the
ledger or used to replace capture failures. Search snippets are exposed evidence,
not independent native material or proof of full article topical coverage.

The prior snapshot contains **8 Physics World article URL identities**, derived
only from the named v37/v41/v42 inputs and old raw links. None of the four new
nominees appears in that bounded snapshot. This does **not** establish complete
prior unfamiliarity, work-level independence or untouched-test status. All new
search text, URLs and captures are now explicitly exposed development material.

The service returned pages whose displayed/native dates are later than the
query cutoff. Date operators alone did not produce a date-compliant pool.
Under the frozen procedure, publication-date eligibility is decided at the
native-capture stage, so those nominees remained in their original slots.

## Complete native outcome

Each occupied slot received one registered certificate-verifying HTTPS curl
route. All **4/4** completed with HTTP200. Maximum body size was 4 MiB, total
time 20 seconds, connect time 8 seconds, and at most three HTTPS redirects per
route. There were no retries, extra searches, web opens/clicks, archive requests,
alternate endpoints or replacement nominees. Complete raw bodies, headers and
receipts remain local; response headers are excluded from public publication.

| Fixed slot | Nominated article | Observed publication date | Direct paragraphs / nonempty | Paragraph characters | Ready | Unmet check |
|---|---|---|---:|---:|---|---|
| q00s00 | [Glashow resonance is spotted in a neutrino detector at long last](https://physicsworld.com/a/glashow-resonance-is-spotted-in-a-neutrino-detector-at-long-last/) | 2021-03-17 | 11 / 11 | 4817 | No | Publication date after 2018-09-30 |
| q00s01 | [Francis Halzen wins Nobel Prize in Physics](https://physicsworld.com/a/francis-halzen-wins-nobel-prize-in-physics/) | 2026-10-06 | 23 / 22 | 6227 | No | Publication date after 2018-09-30 |
| q01s00 | [Drilling down to catch cosmic rays at the South Pole](https://physicsworld.com/a/drilling-down-to-catch-cosmic-rays-at-the-south-pole/) | 2014-10-26 | 12 / 12 | 8537 | Yes | None |
| q01s01 | [Looking at the sky from under water](https://physicsworld.com/a/looking-at-the-sky-from-under-water/) | 2017-11-20 | 21 / 21 | 13193 | No | No h1; single_matching_h1 false |

Dates above are observed `article:published_time` metadata in these exact saved
responses, consistent with the displayed dates returned by discovery. They are
not authentication of bytes available at the historical publication date. Article
titles are observed publisher labels, not separately validated scientific claims.

Native URL/canonical identity, HTML/body/container checks, paragraph mapping,
minimum text scope and topical checks passed for all four captures. The two
date failures had matching h1 titles. The 2017 candidate's **empty h1 inventory**
is a structural observation, not a contradictory title or failed HTTP capture.
No alternate title field was used to rescue it after the result.

All original direct p children in the unique
`article[id^="post-"] > div.entry-content` were retained, including the empty
paragraph in q00s01. Nested newsletter forms/cards, navigation and surrounding
layout were excluded by that fixed structural rule. Every nonempty paragraph
maps uniquely to its saved stripped-script body with original Unicode spans.
The scope ledger is in the local [observations](../data/v50/observations/).

## What this adds and what remains unmet

The result adds **one captured, scope-feasible candidate for a future registered
comparison**, not four admitted controls. The other three failures remain in
the four-slot denominator. HTTP success is **4/4**, readiness is **1/4**, and
the four-ready planning capacity is false. This intake target is separate from
the old four-work independently reviewed natural-benchmark requirement, which
also remains unmet; no independent source group or untouched unit is admitted.

These are topical alternative candidates, not certified false parents. Article
selection may capture related reporting or shared sources; ancestry and source
group relationships were not established. No word meaning, immediate FL source
identity or translation follows. There are **zero scaffold/alignment scores**,
zero new numeric inventories and zero opaque lexical/semantic scores in this
experiment. All previous scores, controls and failed gates remain unchanged.

## Verification and next step

**382/382 full-workspace tests** and **343/343 isolated-public-export tests**
pass; the same 39 archive-dependent tests remain excluded publicly. Nine new
fixtures cover exact native URL safety, whole-word topic checks, supported
response/header attribution, first-appearance order and prior exposure, fixed
slot caps/empty slots, publication-date failures, native identity/title/challenge
checks and unique direct-paragraph mapping.

The [separate verifier](../scripts/verify_publisher_intake_v50.py) reconstructs
the bounded exposure snapshot, both saved search calls, all 31 returned blocks,
every nomination/slot, four request receipts and the critical native checks from
saved bytes. It checks all **49 prior manifests and deliverable seals**. It
shares BeautifulSoup html.parser with acquisition and is same-agent engineering
verification, not independent review. See the
[verification receipt](000050_verification.json) and local
[immutable report](../runs/000050_publisher_intake/report.json).

No new source identities, semantic labels, independent reviews, independent
groups, false-parent certificates or untouched natural test units are admitted.
Scientific acceptance and semantic metrics stay null. Public code/tests/protocols
and this report are separated from local raw acquisitions, search responses,
headers and generated evidence under the standing publication boundary.

Next bounded step: register an **offline identity/heading-layout audit of
q01s01**, using only these saved bytes. Determine where the title is represented,
how it relates to canonical/metadata identity, and whether the direct-paragraph
scope is complete under the current representation. Retain the failed h1 gate
as written; any future eligibility rule requires a new registration. Preserve
the ready q01s00 capture without scoring or replacing slots. A future intake
can improve explicit date screening before native nomination, but that change
must not be applied retrospectively to this experiment.
