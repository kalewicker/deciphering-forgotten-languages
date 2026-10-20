# Experiment 59: offline publisher-native discovery preflight

## Question and exposure

Does the frozen publisher HTML explicitly declare a native search route that
can be probed under a fixed budget? E58's two engine searches filled neither
nomination slot. That discovery failure and the unevaluated three-distinct-type
requirement remain unchanged. This experiment makes **zero network requests**.

Before registration, the reference capture was inspected: its GET-default form
has action `https://physicsworld.com`, input `s`, and a JSON-LD SearchAction has
`https://physicsworld.com/?s={search_term_string}`. This is a disclosed development
audit, not a blind endpoint prediction. The other ten captures are fixed by
provenance, including failed article admissions and later alias responses. There
are 11 captures of seven distinct article URLs; repeated templates are not 11
independent sources. No captures are omitted because of their prior outcomes.

## Fixed extraction and decision

Freeze every raw body and receipt: reference E42, four E50 originals, four E53
alias-response captures, two E55 originals. Inventory all forms containing an
input/control named `s`, retaining DOM form indices and control metadata. Never
save password or hidden-control values in the extracted ledger. GET is the HTML
default if method is absent. Require explicit action resolving to HTTPS exact
physicsworld.com root, default port, no credentials/query/fragment. A single
named control must be an enabled text/search input `s`; reject base href,
external associated controls, form attributes, submit overrides, extra/duplicate
named controls and POST. Relative actions are resolved against the saved URL.
All candidates must pass; do not choose a convenient form among conflicting ones.

Recursively inventory every SearchAction in every application/ld+json script,
with script index and JSON path. Require the exact observed EntryPoint template
and required PropertyValueSpecification for search_term_string. Malformed JSON
or unsupported/conflicting actions fail the page. Require at least one supported
form AND one supported action, and all declarations to agree. The uniform gate
requires every one of the 11 captures to pass; retain the full denominator on
failure. Query is fixed as literal **ANITA**, encoded by standard URL query
encoding. No date or numeric filters are assumed to exist.

Also inventory declared API-root, alternate article-JSON and oEmbed links with
DOM indices, but never derive search endpoints from WordPress conventions. No
external scripts, form instructions or document text are executed.

## Concrete next probe contract, not an executed acquisition

If the uniform declaration gate passes, the only proposed next network step is
one GET `https://physicsworld.com/?s=ANITA`. Maximum one application response,
zero retries and redirects, 8 s connect / 20 s total, 4 MiB body limit, no
credentials, cookie jar, JavaScript or additional assets. Save an intent before
the attempt, raw body/headers, telemetry and SHA-256 receipt; retain any failure
without a replacement route or query. A redirect is recorded and not followed.

The response inspection is static and descriptive: HTTP/transport/content-type,
HTML title, every h1/h2, all search-form declarations and every `<a href>` in DOM
order, retaining literal href and anchor text and resolving relative hrefs
against this fixed request URL. Base href makes link resolution unsupported.
Keep all occurrences and rejection reasons; apply the unchanged E55 strict
article-URL predicate only as a diagnostic. An HTTP200 or a navigation link does
not establish a search hit. Search-result container selectors are **unregistered
and untested**, since no search response exists in this cohort. Thus this probe
cannot nominate candidates, follow pagination/links, acquire articles, or score
numbers. A new registration must define result attribution from the saved
response before a later intake. Challenge/redirect/error responses are retained
as probe failures. No probe is authorized by this offline runner itself.

## Verification and stop

Run adversarial declaration fixtures, an offline replay that does not call the
production audit, hash-check all 58 previous runs and deliverable seals, and the
full local and isolated-public suites. A second code path shares the HTML parser
but is not an independent human or scientific review. Seal the new artifacts,
checkpoint local evidence and publish only code, protocol and small reports.
Stop after this preflight. Declaration agreement is not live endpoint usability,
validated search-result parsing, harder-comparator availability, quantity
correspondence, opaque FL semantics, source identity, or benchmark admission.
