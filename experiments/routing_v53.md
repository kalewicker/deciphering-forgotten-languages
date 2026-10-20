# Experiment 53: four frozen Open Graph endpoint routes

Prospective bounded routing diagnostic after E52. Test every one of the four
stored v50 og:url values, in original slot order, including both failed dates
and the missing-h1 page. Do not assume aliases from similar slugs. Freeze exact
endpoints, old canonical URLs, titles, bytes, readiness and all 52 prior manifests
and available seals in the config; freeze config/code/tests in preflight before
the first request. No new discovery, replacement endpoint or retry.

Budget: exactly four native curl route attempts, one GET route per endpoint;
at most three HTTPS redirects per route (at most sixteen application requests
if every redirect limit is exhausted). Proxy CONNECT and informational header
blocks do not count as publisher responses. Eight-second connection timeout,
twenty-second total timeout, 4 MiB body cap, TLS verification enabled, compressed
transfer/content decoding, no script execution, form submission, credentials or
cookie persistence. Existing environment transport/proxy settings are retained.
Curl configuration files are disabled and retry count is zero. Redirects may be
followed to HTTPS locations, but any non-publisher hop fails the support rule.
Capture raw headers, decoded body, curl telemetry, command, UTC times and hashes
privately. Keep timeout, non-200, malformed and partial responses in denominator.

Parse status and Location chains from saved headers, ignoring only CONNECT
"Connection established" and 1xx blocks. Require consistent redirect count,
recognized 301/302/303/307/308 intermediates with exactly one Location, final
200 without Location, final URL matching the reconstructed chain, and publisher
HTTPS URLs at every hop. URL equality retains the /a/ distinction, permits only
default port and trailing-slash variation, and rejects credentials, queries,
fragments and escaped/non-article paths. No URL normalization inserts /a/.

For per-route support require complete curl success, status 200, HTML content
type, consistent chain, one or more canonical fields all matching the frozen
canonical endpoint, and all three title channels present and matching the frozen
title: HTML title, og:title and Article/NewsArticle JSON-LD headline. Every value
in those channels must agree; malformed JSON-LD fails this diagnostic. Strip only
the final Physics World service suffix, then NFC/casefold/whitespace-normalize
titles. Fields from one response are not independent corroboration. Log current
og:url, h1 and publication metadata without treating them as acceptance gates.
An observed article title is a label, not independent verification of its claims.

Classify supported routes as (a) observed redirect to the frozen canonical URL,
with at least one redirect, or (b) observed served alias at the exact requested
alternate URL, without redirects and with matching canonical/title metadata.
Anything else remains unresolved, even if only some checks pass. The cohort
gate passes only at 4/4 supported; report every check, category and denominator
regardless. Raw-body equality with old captures is descriptive, not required:
different live bytes cannot authenticate historical bytes or routing.

Retain all E50/E51/E52 failures and decisions. No h1/date exceptions, readiness
promotions, old URL-diagnostic rewrites, scaffold/lexical scoring or FL meanings.
This does not admit immediate source identity, independent review or untouched
test units. It cannot meet natural-benchmark capacity. Stop after these routes
and accounting verification. Follow-on work requires a new registration.

Verify recorded command limits, input/output hashes, timing and route count;
reconstruct header chains and metadata checks with a separate implementation
against the saved captures (no verification requests). Verify all prior run
manifests and deliverable seals. Same-agent verification and shared HTML parsing
are engineering limits, not independent scientific review. Publish protocol,
code, tests and summary/verification reports only; raw evidence stays local.
