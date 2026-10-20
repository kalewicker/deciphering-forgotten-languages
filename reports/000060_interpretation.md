# Experiment 60: native search returns a complete static HTML observation

The single registered GET `https://physicsworld.com/?s=ANITA` completed with
**HTTP200, zero redirects, and 106,103 body bytes**. Exactly one application
response was recorded. All eight registered transport/HTML checks pass,
including the exact final URL, agreeing HTML Content-Type, nonempty body within
the 4 MiB limit and absence of the five fixed challenge signatures. There were
no retries, alternate queries, pagination, asset requests or article captures.

The page title is “You searched for ANITA – Physics World”; a heading says
“Results for: ANITA”, and a text/search input echoes the literal query. These
are direct observations of this saved response. They do not measure search
precision, recall, ranking stability or whether a listed page qualifies as a
harder comparator.

| Static inventory | Count |
| --- | ---: |
| HTML titles | 1 |
| h1/h2 headings, including navigation/filter headings | 7 |
| Forms containing a control named s | 2 |
| SearchAction declarations | 1 |
| base href declarations | 0 |
| All a[href] occurrences | 115 |
| Occurrences passing the unchanged E55 article-URL diagnostic | 18 |
| Distinct article-shaped URLs in those occurrences | 9 |
| Repeated article-URL occurrences retained | 9 |
| Search hits attributed / candidates nominated | 0 / 0 |

All anchors remain in DOM order, including empty anchor text, navigation and
repeated title/read links. A strict article-shaped URL is a diagnostic, not a
search-hit classification or article admission. The ledger includes tag indices
and ancestor tag/id/class metadata. For example, anchor index 47 at global tag
index 384 has a `h3.listing-block__title` ancestor inside an `article.listing-block`
under the main content container. This is observed markup for a future parser
design, not a selector applied here. The result-container selector remains null.

The inventory retains both search-related forms and all of their declaration
checks. E59's strict form agreement is not an E60 observation gate: the response
may include additional controls and forms. Only text/search inputs named s have
values recorded in the extracted ledger; hidden/nonce/password values are not
copied there. Raw HTML, headers, complete curl telemetry, stderr, the intent,
receipt and layout ledger stay in local `data/v60`.

Body SHA-256:
`06236aa910755b5d50b21fe40e090fb3d0aabe177dbe8873431ad7ea6829f81f`.
The E59 future contract was copied verbatim, including its historical proposal
status and lack of an earlier live fixture. E60's intent, receipt and completed
run manifest record the actual attempt; the copied proposal fields are not the
current execution status.

## What changed and what remains unresolved

E59's declared route is now evidenced to return one complete direct HTML page
with query-labelled markup. E58's external-search failure remains unchanged.
No result attribution, candidate selection, article eligibility, three-distinct-
numeric-type test, new scaffold comparison or semantic score was performed.
The reference and all earlier captures/failures remain fixed. Every viewed
link/text is development exposure; no untouched test unit or independent source
work is admitted. Native search function is not validated beyond this one
response observation. Opaque meanings, quantity correspondence, immediate FL
source identity and independent scientific review remain unresolved; natural-
benchmark capacity remains unmet.

## Verification and next step

Seven new fixtures pass. **455 local tests** and **416 isolated-public snapshot
tests** pass; 39 archive-dependent cases remain explicitly excluded from the
public runner. The separate verifier replays all 115 anchors, headings, titles,
base handling, checks, counters, command, timing, intent, receipt, telemetry and
budget. It does not import the v60 production functions. It shares BeautifulSoup,
the sealed E55 URL predicate and E59 declaration audit, so this is a separate
code path, not independent scientific review. All **59 prior runs and historical
deliverable seals** remain intact. See [verification](000060_verification.json).

Next: register one **offline search-result attribution audit** against this exact
saved body. Define and test a conservative container/title-link/date/snippet
schema from the observed layout; account for all 115 anchor occurrences, duplicate
links and out-of-container links; preserve every malformed or conflicting unit
and prior exposure. Do not acquire another page, follow pagination, nominate
articles or score numbers during that audit. Only a later registered intake
could consume attributed development candidates. No additional research request
is part of E60.
