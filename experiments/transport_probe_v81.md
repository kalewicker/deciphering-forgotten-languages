# E81: bounded infrastructure capability check

E80 failed before HTTP with curl35 and a TLS protocol-version alert. Offline
inspection found only /usr/bin/curl (curl8.7.1, LibreSSL3.3.6/SecureTransport) and
Python's OpenSSL3.5.5. No proxy environment variables or urllib proxy settings
were present. This is design context, not evidence of a cause.

Freeze protocol, code, client identities and E80's seal before four fixed HEAD
attempts, in order: system curl to https://example.com/; Python urllib to that
same URL; system curl to
https://forgottenlanguages-full.forgottenlanguages.org/robots.txt; Python urllib
to that same URL. One attempt per cell, no retries, redirects, fallback, protocol
version changes, packages, certificate changes, credentials or proxy changes.
Use a fixed E81 user-agent. TLS verification stays enabled. Use an 8s connect/20s
whole-operation curl limit; Python gets a 20s socket timeout and an outer 22s
process deadline (curl also has the 22s outer bound). Retain partial failures.

HEAD requests request no response body; never read/store a body even for HTTP
errors. Save intent, stdout/stderr, headers/structured response metadata, client
versions, timestamps and return codes locally. Curl's headers are raw; urllib's
are parsed header pairs, not wire bytes. Reject any response metadata over64KiB
for interpretation while retaining the command output as diagnostic evidence.
Do not fetch the label page, posts, archives, images or other destinations.

Freeze the absence of proxy configuration; stop without research requests if
proxy presence changes before launch. Do not silently bypass configured proxies.
Use the normal verified SSL context, not an unverified context. Python does not
load netrc or install authentication handlers. Record certificate environment
variable presence and reject overrides for this diagnostic. Preserve E80 exactly.
Execution may require outer sandbox approval; E81's two clients must run under
the same approved execution setting. Do not claim that comparison with E80
isolates its execution environment or any single TLS-library difference.

Classify every cell as http_response_observed only when complete client evidence
reports an HTTP status100..599 for the exact requested URL with no redirects and
within limits. HTTP4xx/5xx still establish completed TLS/HTTP exchange, not page
availability. A redirect is recorded but never followed. Otherwise classify
transport_unresolved. Retain error text without asserting client/server blame.
Report both controls, both target results and full4-cell denominator. Do not
interpret endpoint-specific success as article-body or label-route success.

If a client obtains a target HTTP response, it becomes a candidate transport for
a separately registered intake, subject to its method/body/identity limits. If
neither does, leave transport unresolved; no automatic client/TLS/host sweep.
No result authorizes retrying E80 or changing E79. This is infrastructure evidence,
not new corpus material, model validation, semantic admission or untouched data.
The separate semantic benchmark remains0/4.

Verify intent order/budgets, commands, hashes, versions, evidence classification
and unchanged E80 seal. Test HTTPerror versus connection-error classification,
redirect handling, output limits and empty/malformed responses using fixtures.
Stop after this one diagnostic, receipt and report. Public code/protocol/reports;
network artifacts and environment details stay on the local evidence branch.
