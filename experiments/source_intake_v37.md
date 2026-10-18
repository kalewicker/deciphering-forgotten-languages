# Experiment 37: bounded source-first intake and review feasibility

Register before live discovery or new acquisition. The outcome is a capacity
ledger, not retrieval accuracy, a translation or a lexical admission. Existing
v36 failure and the zero-of-four natural-capacity decision stay unchanged.

## Budget and fixed nomination

Run exactly these four metadata-discovery searches in order, at most once each:

1. `site:forgottenlanguages-full.forgottenlanguages.org "arxiv.org"`
2. `site:forgottenlanguages-full.forgottenlanguages.org "doi.org" "2025"`
3. `site:forgottenlanguages-full.forgottenlanguages.org "References" "2026"`
4. `site:forgottenlanguages-full.forgottenlanguages.org "Bibliography"`

Retain every returned hit and its ordering, including unavailable/duplicate hits.
Take the first two distinct dated post permalinks per query from returned organic
results on that exact hostname, excluding URLs already acquired or selected in
project JSON manifests. Do not fill missing slots from a third result. A post
mentioned only in an unstructured search narrative is not an eligible result.
Up to eight post nominees remain in the fixed denominator. Deduplicate across
queries in first-appearance order; shared/exposed candidates remain in a rejection
ledger. Search snippets are possible target-prose exposure and must be recorded;
none of these posts is automatically an untouched test unit.

Fetch each nominated post once, HTTPS with certificate verification, no cookies,
credentials, login, retries or access-control bypass. Timeout 20 seconds,
connect timeout 8 seconds, maximum three HTTPS redirects, 4 MiB post limit.
The purpose is citation-metadata extraction before inspecting target prose.
Save received bytes, all response headers, times, effective URL, failures and
hashes. Require one `div.post-body`, title, permalink identity and no challenge
page before exporting a normalized body for later review. Full-body acquisition
does not establish whole-source coverage. Do not display or compare opaque
paragraphs in the prediction process during this intake.

Extract public scholarly citation links from within that body, in document
order: DOI links, arXiv abstract/PDF links, and direct PDF links on publisher,
author, university or established institutional repository hosts. Treat image,
navigation, donation, social and purchase links as ineligible. Keep all links
and rejection reasons. Generic links without a work identifier are not sources.
Use the linked citation text/DOI/arXiv identifier to nominate works without
importing proposed English translations, glosses or public dictionaries.

Choose at most four distinct works in post/link order. Reject a known work,
edition/mirror, duplicate identifier or component connection using the existing
exposure inventory and previously saved source URLs/titles. Record uncertainty:
an unseen URL alone does not prove a new independent work. Do not replace a
chosen work after transport failure or missing prose. If metadata cannot resolve
four works, retain the shortfall. No title-similarity or correspondence score.

## Source-first material routes

For each chosen work, freeze its exact linked source URL before acquiring it;
one source attempt, 20 seconds, 8-second connect timeout, three HTTPS redirects,
20 MiB maximum. DOI resolves the linked publisher record as given; arXiv abstract
URLs may deterministically map to `https://arxiv.org/pdf/{id}` before the request.
No guessed PDF endpoints, mirrors, alternate editions, follow-up web searches,
automated downloads behind subscriptions or retries after denial. A landing page
or abstract alone is metadata, not full source prose. All selected works and
failed attempts stay in the denominator. Maximum raw attempts: eight posts plus
four sources. Search-discovery calls are separately counted (four).

If raw transport fails on a nominated FL post, allow one fixed indexed browser
open of that exact URL as a fallback, up to eight in total. Clearly label it
indexed extraction, never current raw HTML. Do not follow its links to discover
replacement targets. Citation metadata may come from an indexed extraction but
the post remains raw-capture-unavailable. If the raw response succeeds but lacks
eligible citation links, do not invoke fallback to find more favorable links.

Inspect source availability/identity before any target/source correspondence
comparison. The acquisition stage can retain raw PDFs without admitting their
text as verified prose. A source must pass edition/authority/coverage and
extraction review before entering a future correspondence benchmark. OCR needs
page-image checking. Save reviewer-facing bundles only when the material needed
for review exists; blank templates and metadata-only records are not reviews.

## Review route and capacity gates

No external reviewer is currently supplied. Prepare a self-contained intake
ledger and, where possible, review material binding source and target artifacts
with a blank declaration of reviewer identity, role, prior exposure, independence,
coverage and uncertainty. A source-disclosed review cannot establish blinded
source retrieval. Another same-assistant comparison is not independent validation.
No external message, upload, hiring or fabricated review is authorized or needed.

Separate candidate novelty (confirmed/provisional/exposed/unknown), capture
availability, source-prose readiness, review readiness, review completion and
untouched status. The original four-work rule requires four independent,
unexposed connected works with two independently reviewed nonoverlapping passage
units each, split two development/two test before scoring. Search snippets and
metadata exposure must be considered before any later test assignment. This
intake cannot erase exposure or supply absent reviewer evidence.

The fixed success question is whether that four-work capacity is now met.
Partial material recovery is reported as engineering progress only. If not met,
report the precise observed shortfall and the next evidence-producing boundary.
Do not score a natural target, train/update a lexicon, expand synthetic alignment,
relax gates or claim semantics. Semantic metrics/scientific acceptance remain
null; accepted source identities, semantic labels, independent reviews and
untouched-test admissions remain zero in this experiment.

## Provenance and stopping

Hash-seal this registration, the current connected/exposed source inventory,
the v36 report/seal and intake implementation before raw acquisition. Preserve
all search results, route receipts, exclusions, sources and representations.
Verify offline that every counted artifact matches its bytes and that every
failure/exclusion remains in the denominator; check all 36 prior manifests and
deliverable seals. No new access route after the budget is exhausted. A failed
capacity gate is a completed experiment, not permission to extend the search.
