# Experiment 60: one native-search response and static layout inventory

## Registration and question

E59/E59a found agreeing form and SearchAction declarations in all 11 saved
publisher captures (seven article URLs). No search response has been inspected.
Does the exact declared route return one complete direct HTML observation under
the frozen budget, and what static markup does it contain? This is a development
layout probe, not a new candidate intake or a test of numeric correspondence.

Copy the entire E59a future_probe_contract verbatim into the new config. Freeze
its protocol, corrected E59 inputs/report/seal, reused helpers, all 59 previous
manifests and all prior seals. Freeze new code and adversarial fixtures in a
preflight before reserving the single attempt. No earlier sealed file changes.

## Exactly one attempt

GET `https://physicsworld.com/?s=ANITA`, curl configuration disabled, HTTPS only,
8-second connect / 20-second total timeout, 4 MiB body limit, fixed v60 user-agent,
zero retries and redirects. Do not use curl --location. No cookie jar,
authentication, JavaScript, assets, robots request, alternate endpoint, search
engine, link following, pagination or query replacement. Git publication traffic
is outside the research request count. Save an intent before launching curl;
reserve the slot permanently even on a transport/HTTP/parse failure. The probe
phase refuses to run if the intent or acquisition directory already exists.

Save raw body (if supplied), headers, complete curl JSON telemetry and stderr
privately, with hashes/byte counts and an exclusive receipt. transport_complete
means curl exited zero with a recorded HTTP status and body within the size
limit; HTTP errors may be complete responses but fail the observation gate.
Retain redirects without following Location. Do not replace any failure.

The observation gate requires transport_complete, HTTP200, exact requested URL
as final URL, num_redirects zero, exactly one consistent application response
(excluding proxy CONNECT and 1xx blocks), no Location, HTML media type agreeing
between telemetry and all final Content-Type fields, a nonempty body within the
limit, and no registered challenge signature in static extracted text. Casefold
and test the fixed literals in config. HTTP200/HTML is not validated search
function or search-hit attribution. Failed checks remain explicit.

## Fixed descriptive parser

Use BeautifulSoup html.parser on the saved body, including failed/partial HTML.
Retain every title, h1/h2 and a[href] in DOM order, with global tag indices and
ancestor tag/id/class metadata. Keep empty text, all duplicate occurrences,
navigation and template links. href means the HTML-decoded attribute value,
not a raw-byte span. Resolve against the fixed request URL, never an inferred
endpoint. Any base[href] disables link resolution for the whole document but
does not remove anchor occurrences. Malformed URLs stay as rejected rows.

Use the unchanged E55 article_key predicate as a diagnostic only; distinguish
strict article-shaped URLs, other URLs, malformed attributes and unsupported
base resolution. Do not classify any link as a search hit or nominate it. Reuse
the sealed E59 declaration inventory for all search forms/actions and retain
text/search input values named s (no password/nonce/other field values). Record
query echo separately, without treating it as functional search validation.

The result-container selector remains null. The static inspection may describe
candidate markup for a future registered attribution parser, but no selector
or result/candidate extraction is implemented in this experiment. Every viewed
link/text is exposed development evidence. No source-group or untouched-data
claim follows, even for previously unrecorded URLs. No article acquisition,
alignment, numeric threshold evaluation or new scientific admission occurs.

## Verification and stop

Fixtures cover one-request command restrictions; navigation, empty and duplicate
anchors; base href and malformed href; direct HTML versus search validation;
redirects, partial bodies, challenges and content-type errors. A separate
verifier must reconstruct the static inventory and checks from saved bytes
without importing the production v60 inventory/observation/summary. It may reuse
the sealed E59 declaration audit and E55 URL predicate, disclosed explicitly.
Verify command/intent/receipt/telemetry hashes, timing and request accounting,
all 59 prior runs/seals, and full local/isolated public suites. Preserve all raw
responses locally; publish code, protocol and small reports, then stop.

If a useful search response is captured, next register an offline attribution
parser against the saved layout, retaining all links/rejections and previous
exposures before any later network intake. If not, retain the failure and plan
a separate bounded diagnostic from the saved response. Neither branch permits
an extra request or a modified selector in this experiment.
