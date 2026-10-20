# E66: one cited arXiv work, fixed version-addressed acquisition

Register before research requests. Select the first syntax-recognized arXiv
identifier in E65's reference-tail order, without topic ranking or replacements.
The only observed candidate is arxiv:0812.0349 (reference 27). E65 exposed its
citation, displayed title Nonlocality without nonlocality, author Weinstein S.,
and year 2008; it did not resolve the work. This is development acquisition.
The citation has no version: choosing v1 below is a prospective edition policy,
not a claim the FL author used v1. E63's failed gate and E62's closure persist.

## Budget and routes

One source slot; at most two routes and two application responses, no retries,
redirects, discovery searches, alternate hosts or fallback versions. First GET
https://arxiv.org/abs/0812.0349v1, once. Require complete HTTP200, HTML content
type, exact final versioned URL, no redirect and all metadata requirements below.
Only if that passes GET https://arxiv.org/pdf/0812.0349v1, once. Limits per route:
8 seconds connect, 30 seconds total, HTTPS only, zero retries/redirects; 4 MiB
HTML and 20 MiB PDF decoded body maximum. Preserve raw bodies, all headers,
curl telemetry/stderr/commands, UTC intent and receipt times, and SHA256 hashes.
A failed/missing route is recorded and not retried for a more favorable result.
Network sandbox failures requiring authorized escalation are environmental
failures, not a license for an unregistered scientific retry after an HTTP result.

## Metadata and edition gates

Require exactly one citation_title matching the displayed citation title after
NFC/case/whitespace normalization only. Require exactly one citation_author with
family name Weinstein and first-name initial S (compatibility with the abbreviated
citation, not independently proved personal identity). Require exactly one
citation_arxiv_id equal to the selected base ID or base ID plus v1. Require one
submission-history container and complete [vN] date inventory: each declared
version has one parseable UTC weekday/day/month/year/time date, unique positive
version numbers, consecutive versions from 1, and nondecreasing submission times
in version order. The v1 date must be in cited year 2008 and before 2013-10-28.
Require exactly one parseable citation_date in 2008. Retain native title,
authors, dates, identifier fields and every history row even on failure. Do not
substitute a search result, infer a missing date, repair a title, or relax a gate.
The live record's version history is a provider claim, not independent evidence
or publication-era FL authentication.

On metadata success, capture the fixed versioned PDF. Require complete HTTP200,
application/pdf, exact final versioned URL, PDF magic, successful pypdf parsing
and 1-40 pages, with pypdfium2 agreeing on page count. Extract the first page
only for identity checks, retaining its original Unicode text and hash. Require
the visible ID 0812.0349v1, normalized expected title, and metadata author in that
page. Render that entire page and inspect the visible title/author/version.
Record the visual decision separately; absence/conflict remains failure. This
is a first-page identity audit, not a full-paper visual/prose review. Freeze full
PDF bytes and first-page derivative even if a later identity gate fails. Never
silently treat the PDF as the FL author's edition. If metadata fails, skip the
PDF and record it as skipped rather than using the unused budget elsewhere.

## Exposure, outputs and stop

Compare the selected base ID to the frozen E63 known-URL registry using the
sealed E37 URL recognizer; retain its incomplete scope. Record E65 preparatory
exposure and this acquisition as development exposure. Absence in the registry
is not proof of a new independent work or untouched evaluation unit. No source
identity relative to opaque FL text, translation, passage matching, lexical
scoring, natural-benchmark admission or independent review occurs.

Freeze registration/inputs/code/tests before acquisition. Bundle routine native
metadata, version history, conditional capture, first-page identity and exposure
checks in this one step. Stop with acquisition_unavailable, metadata_mismatch,
pdf_identity_unavailable, or version_addressed_development_pdf_available. Preserve
all failures and the one-slot denominator. A separate same-agent verifier checks
selection, gates, receipts/limits/timing, complete output inventory and all 65
prior run manifests/seals; it is not independent scientific review. Public main
gets code, tests, registration and small reports only; responses/derivatives stay
local. Any next passage test needs a fresh fixed-scope comparison registration.
