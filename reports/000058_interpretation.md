# Experiment 58: fixed harder-comparator search leaves both nomination slots empty

The registered intake supplies **0 qualifying harder comparators out of two
slots**. Both searches completed, but all **25 attributable results** fail
nomination: **21 invalid article URLs** and **four missing the required topic
terms**. Both slots remain empty. The feasibility gate is false, and the run
stops at its two-search budget without retries or replacement searches.

This is a **discovery-stage failure**, not a measured numeric-overlap failure.
There are **zero native or alternate-URL requests, zero new captures and zero
candidate numeric inventories**. The three-shared-type threshold was never
evaluated on a new candidate. The result does not establish that closer
comparators are absent from the publisher or the wider literature.

## Frozen protocol, exposure policy and request accounting

The [registration](../experiments/hard_comparator_v58.md), config and code/tests
were frozen before either search, with **121 input hashes**, all **57 prior
manifests** and available deliverable seals. The prior snapshot contains **50
article URLs**, extending the E55 registry with all E55 results and links/identity
declarations in its two native captures. It excludes all **seven previously
captured article URLs**, including the known reference, late-date/missing-heading
cases and the two E55 pages. No failed page was recaptured.

Unlike E55's broader exclusions, E58 explicitly permits previously linked or
search-only leads with their exposure tags retained. Those are labeled exposed
development leads, not untouched tests or independent sources. This prospective
policy does not rewrite an earlier nomination. No hit in this actual run was
rejected because it was previously captured; the observed bottleneck is returned
URL/topic eligibility.

Each of the two fixed queries was sent once, sequentially, with one search_query
and long response. Exact requests, intents, UTC times and responses are local in
the [discovery evidence](../data/v58/discovery/). No query repair, extra filter,
retry, open, click, archive lookup or additional discovery route was used.
Quoted numerals and date/site operators were planning hints; their enforcement
was never assumed from the query text.

| Query's numeric/topic emphasis | Attributable blocks | Invalid article URL | Topic terms missing | Nominations |
|---|---:|---:|---:|---:|
| ANITA, `96`, `40` | 13 | 10 | 3 | 0 |
| Antarctic neutrino, `180`, `2006` | 12 | 11 | 1 | 0 |
| **Total** | **25** | **21** | **4** | **0/2 slots** |

The article-URL rule requires exact HTTPS physicsworld.com with one /a/ ASCII
slug and no credentials, query, fragment or nonstandard port. Each of the four
valid article URLs lacks the required whole-word combination in its complete
returned title/block: neutrino/neutrinos AND ANITA/Antarctic/Antarctica. They
were not silently treated as topical because the query contained those words.
Every block, span/hash and decision remains in the local
[selection ledger](../data/v58/selection.json).

First-appearance tracking and the one-nominee-per-query cap remain unchanged.
The selection and capture preflight freeze two empty slots and an empty native
request list. No acquisition or alias-acquisition directory was created. Unused
native/alternate allowances were not spent on replacements: the maximum was
two initial routes plus at most two conditional observed-alternate routes, each
with E53's unchanged TLS/HTTPS, retry-zero, 8/20-second timeout, three-redirect
and 4 MiB limits. None of those native branches was exercised in this run.

## What was registered, but not reached

A qualifying candidate would have had to pass all fourteen E54 intake checks,
including **[2000-01-01, 2018-09-30]** publication dates, consistent titles/URLs,
the original paragraph representation and volume/topic requirements. An exact
observed alternate could have acquired E53-style routing evidence with explicit
v58 provenance. No date, title, scope or transport exception was registered.

The numeric requirement is **at least three distinct literal numeric types from
the entire unchanged E56 masked-target inventory**, after E52 paragraph scoping
and E46 quotation/boundary rules. It is not a repetition count and not limited
to the six reference-shared types audited in E57. A native failure could not be
rescued by numeric overlap, and unsupported quotation syntax would remain an
unavailable numeric representation. No decimal, year, unit or symbol repair was
allowed. These rules were fixture-tested; no new native candidate reached them.

The gate required at least one qualifying candidate from the two frozen slots.
Both empty slots count as failures. No LCS/window/control score was computed,
no comparison panel was expanded, and the threshold was not lowered after the
negative result. This intake cannot estimate source-absence detection or the
prevalence of high-overlap pages.

## Verification, preserved results and next boundary

**439/439 workspace tests** and **400/400 isolated-public-export tests** pass;
the same 39 archive-dependent tests remain excluded publicly. Six new fixtures
cover the exact three-type boundary, repeated-key inflation, native date-failure
precedence, quote masking/literal punctuation, unavailable representations,
captured-versus-search-only exposure and empty slots/caps. Conditional capture
behavior also retains the earlier E53–E55 checks; it is not claimed as live-tested
by E58's empty-slot outcome.

The [separate verifier](../scripts/verify_hard_comparator_v58.py) reconstructs
the 50-URL exposure snapshot, seven captured exclusions, all 25 result-block
decisions, both empty slots, exact request arguments/timing and the empty native
request list. It checks the complete seven-file local run-evidence inventory,
absence of capture artifacts, report arithmetic and all **57 previous runs and
deliverable seals**. It does not use production nomination and makes zero
requests. See the [verification receipt](000058_verification.json). HTML parsing
is shared and this is same-agent engineering verification, not independent review.

E50's **1/4** and E54's **2/4** capacity failures, E55's **four eligible captures
across six retained slots**, E56's **6 versus 0, 1, 1, 0**, E57's thirteen-context
audit and earlier synthetic failures all remain fixed. These two harder-intake
slots are a separate feasibility denominator, not replacements or retroactive
changes to those cohorts. Scientific acceptance and semantic metrics remain
null; natural-benchmark capacity remains unmet. No meanings, immediate source
identities, independent reviews, certified false parents or untouched units are
admitted.

Next bounded step: an **offline publisher-native discovery preflight** using
only endpoint/form/link declarations already present in saved publisher HTML.
Identify a concrete, attributable native discovery route and register its exact
request/parser/budget before any new network call. This addresses the observed
general-search nomination failure while keeping the three-type requirement and
old results intact. If no usable native route is evidenced, retain that failure;
do not invent endpoints or continue open-ended query tuning. No such endpoint
audit or request was performed as part of E58.
