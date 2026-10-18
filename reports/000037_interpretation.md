# Experiment 37: one source recovered; natural benchmark capacity remains unmet

The bounded intake recovers **one new provisional citation lead and its source
PDF**, but does not meet the four-work natural-benchmark capacity rule. None of
the four nominated FL posts could be captured directly; three indexed browser
responses were available and one failed. No reviewed passage correspondence,
source relationship, word meaning or untouched test unit is admitted.

The [provisional intake bundle](../data/v37/source00_intake_bundle.zip) contains
the unchanged source PDF, source title-page image, indexed target response,
acquisition receipts, a material manifest, limits and an unfilled review form.
Its state is explicitly **provisional intake, not review-ready**. No reviewer was
assigned or contacted.

## Fixed sample and outcome

Four registered searches targeted explicit arXiv links, DOI links with 2025,
references with 2026, and bibliography. The DOI/2025 and References/2026 searches
returned no results. This is a bounded search outcome, not evidence that those
kinds of posts or sources do not exist.

| Stage | Fixed capacity / selected denominator | Observed |
|---|---:|---|
| Search executions | Four query strings | Eight executions, including preserved unattributed batch |
| Post nomination slots | 8 | 4 nominated; 4 unfilled |
| Direct FL capture | 4 nominees | 0/4; all curl35 TLS failures before HTTP |
| Exact-URL indexed fallback | 4 opens | 3 responses; 1 fetch error |
| Explicit new scholarly source-link slots | 4 | 1 selected; 3 unfilled |
| Selected source acquisition | 1 | 1/1 HTTP200, complete PDF bytes |
| Independently reviewed new works | Four-work capacity rule | 0/4 |

Nomination used the first two eligible dated post permalinks per query, with
prior-URL and duplicate checks. Archive/month listings were excluded. No extra
post replaced a failed capture or a post without an eligible link.

| Nominee | Search route | Direct capture | Indexed fallback | Eligible new source links selected |
|---|---|---|---|---:|
| post00: What was what ANITA really saw? The difficult coexistence at Antarctica | arxiv.org | TLS failure | Available | 1 |
| post01: Quantum Semantic Fields and Universals | arxiv.org | TLS failure | Available | 0 |
| post02: Idfala ať Adfhaffťa Utsid | Bibliography | TLS failure | Fetch error | 0 |
| post03: Elam (Emer Elamita) Bibliography | Bibliography | TLS failure | Available | 0 |

The full [nomination ledger](../data/v37/nominations.json) retains every organic
hit, ordering, exclusion and empty slot. The raw TLS failures are preserved in
`data/v37/acquisition/`; indexed artifacts remain separate in
`data/v37/fallback/`. The [fallback status supplement](../data/v37/fallback_status.json)
distinguishes three available responses from the post02 error. The execution
metadata calls all four fallback attempts indexed representations; that does not
mean all four produced usable page text. None proves a complete, raw or current
FL capture. The TLS failures do not establish their root cause or universal
inaccessibility of the site.

## Recovered lead and what it establishes

The explicit arXiv URL in the indexed [ANITA post](https://forgottenlanguages-full.forgottenlanguages.org/2018/10/what-was-what-anita-really-saw.html)
identifies hep-ph/0209057v1. Its frozen source request is
<https://arxiv.org/pdf/hep-ph/0209057v1>, derived deterministically from the cited
abstract URL, with no alternate endpoint or mirror. The source title page reads
*Neutrino Radar*, Prasanta K. Panigrahi and Utpal Sarkar, September 2002; the
visible version marker is 5 Sep 2002. The downloaded PDF contains eight pages.
The [identity inspection](../data/v37/source_acquisition/source00/identity_inspection.json)
binds those observations to exact bytes, PDF metadata and a rendered first page.
This was the same assistant's engineering check, not independent passage review.

Only the title page's legibility/identity and total page count were checked;
remaining page layouts, extraction offsets and source coverage were not reviewed.
PDF magic, a parseable file and a matching identifier do not themselves verify
source prose for a parallel benchmark.

The identifier and URL were absent from the saved exposure snapshot. Novelty is
therefore **provisional**, not confirmed work-level independence. Mirrors,
editions, composite source connections and citation scope still require review.
The paper is one item in the post's bibliography; its presence does not establish
that it supplies an immediate source passage, let alone the whole post.

The source rule deliberately required an explicit DOI/arXiv link or an allowed
direct PDF URL. Plain bibliographic citations and bare identifiers were not
resolved by new searches or guessed endpoints. Three empty source slots therefore
reflect this acquisition procedure, not absence of other works. A later
identifier-resolution procedure needs its own frozen selection and request budget.

Search results and indexed target prose were exposed during discovery. The
acquired material cannot be relabeled as an untouched evaluation fold for this
process. Language scope, passage boundaries and independent source-group status
remain unresolved; no Kamri or other lexical model was transferred to it.

## Review feasibility and stopping decision

The blank declaration asks a future reviewer to state identity, human/automated
role, prior exposure, independence, source relationship, coverage, exact evidence,
counterexamples and uncertainty. It contains no proposed translations or
word-gloss answers. There is currently no assigned independent reviewer and no
completed return. The bundle can support preparation or scoped material review;
it is not an independent validation packet with established parallel passages.

The original minimum remains four independent unexposed works, two development
and two test, each with two independently reviewed nonoverlapping passage units.
This intake supplies **zero qualifying works**. Engineering recovery of a PDF
does not relax that criterion. No natural target was scored and no old group was
reclassified. The failed v36 near-copy/source-absence gate remains failed.

The next bounded evidence-producing step is to seek an adequate dated,
byte-bound target capture for **post00 only**, then perform a scoped material and
citation review of this fixed lead. First establish what source material is
actually available and whether the citation supports any inspectable passage
relationship; preserve uncertain outcomes. Do not assume an English source
sentence supplies a meaning for the opaque text. An independent review route
remains a separate unresolved requirement for scientific admission. Do not add
aligner features or extend this experiment's search budget to fill its slots.

## Discovery interface repair and verification

The initial batch request returned one flat list without per-query attribution.
It is saved in `data/v37/discovery/search_batch_raw.json` and excluded from
nomination. Before raw acquisition, a [registered interface revision](../experiments/source_intake_v37_discovery_revision1.md)
repeated the same four query strings individually. Total search executions rose
from four to eight under that explicit revision; no search terms, raw-route
budget, candidate rule or capacity gate changed. All extra exposure remains
recorded; the initial batch is not a second candidate pool.

The individual search records' `requested_at_utc` fields were stamped when the
response was saved, immediately after the call, rather than at network start.
They establish response-recording order only. Raw curl receipts separately save
actual request start/finish times; no search latency is inferred from those fields.

Registration preceded live discovery. Revised discovery records, prior exposure,
nominees, implementation and inputs were sealed before raw requests. Source
selection and its exact URL were frozen before the one source attempt. Every
attempt used certificate-verifying HTTPS, fixed limits and no retries or access
control bypass. All source and target failures remain in their denominators.

All **323 tests pass**. Offline verification independently reconstructs post
nomination and checks artifact hashes, routes, request limits, timestamps,
capacity accounting and all **36 prior run inventories and deliverable seals**.
Citation metadata parsing is shared with execution; the verifier explicitly does
not claim independent source-identity or semantic validation. The bundle ZIP was
also checked member-by-member against its manifest and its source PDF is byte-
identical to the acquisition. The [verification receipt](000037_verification.json)
passes while the capacity gate remains unmet.

Scientific acceptance and semantic metrics remain null. Accepted source
identities, semantic labels, independent reviews, untouched-test units, natural
rescores, lexicon changes and external messages remain zero.

Artifacts: [registration](../experiments/source_intake_v37.md),
[preflight seal](../data/v37/preflight.json),
[source selection](../data/v37/source_selection.json),
[capacity ledger](../data/v37/capacity_ledger.json),
[bundle README](../data/v37/intake_bundle/README.md),
[immutable report](../runs/000037_source_intake/report.json),
[manifest](../runs/000037_source_intake/manifest.json).

Verify offline with `.venv/bin/python scripts/verify_source_intake_v37.py`.
Do not rerun acquisition into the existing evidence directories.
