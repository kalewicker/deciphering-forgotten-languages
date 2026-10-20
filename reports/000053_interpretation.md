# Experiment 53: all four stored alternate endpoints redirect to their canonical article

All **4/4 frozen og:url endpoints** returned **HTTP 301**, each with one Location
pointing to its saved **/a/** canonical article URL, followed by **HTTP 200**.
Every resulting page supplied matching canonical metadata and all three
registered title channels. The current-alias diagnostic passes at **4/4**; no
route remains unresolved. This resolves the bounded current-routing question
raised by E52, without changing its strict string/URL diagnostic.

The original E50 intake remains **1/4 ready**, with capacity unmet. Both
out-of-window dates and the missing-h1 failure remain. No opaque meanings,
immediate FL source identities, independent reviews or untouched test units are
admitted. Scientific acceptance and semantic evaluation metrics remain null.

## Registration and complete route accounting

The [registration](../experiments/routing_v53.md) and config freeze the four exact
stored endpoints in original slot order, expected titles/canonical URLs, old
body hashes/readiness and **111 input hashes**. Inputs include all **52 prior
run manifests** and available deliverable seals. Config, acquisition/assessment
code and eight fixture tests were sealed in preflight before the first request.
The separate verifier was written after capture.

There were exactly **four curl route attempts**, with **four redirects and
eight recorded application responses**. Each used at most three HTTPS redirects,
an eight-second connection timeout, twenty-second total timeout and 4 MiB body
cap. No retries, substituted URLs, discovery/searches, browser renders or form
submissions occurred. Curl configuration files were disabled; no credentials or
persistent cookie jar were supplied. Ordinary environment transport settings
were retained. Proxy CONNECT header blocks are distinguished from publisher
responses. Raw response bodies, headers and curl telemetry remain local.

| Frozen slot | Observed route | Canonical and all three title channels | Original E50 readiness |
|---|---|---|---|
| q00s00: Glashow report | 301 → saved canonical → 200 | Match | False: publication after cutoff |
| q00s01: Halzen report | 301 → saved canonical → 200 | Match | False: publication after cutoff |
| q01s00: South Pole report | 301 → saved canonical → 200 | Match | True under original rule |
| q01s01: under-water report | 301 → saved canonical → 200 | Match | False: no h1 |
| **Denominator** | **4/4 redirect routes; 0 served aliases; 0 unresolved** | **4/4** | **1/4** |

For every slot, the exact requested endpoint is its frozen canonical URL with
the **/a/** segment absent. The Location value restores that segment and matches
the saved canonical endpoint. This relationship was observed in the responses,
not inferred from the slug. Original requests, Locations, resolved chains, final
URLs and each individual check are retained in the local
[route ledgers](../data/v53/) and [immutable report](../runs/000053_routing/report.json).

All five per-route checks pass: complete 200, HTML content type, consistent
publisher chain, every canonical field matching the frozen canonical, and every
value in the three required title channels matching the frozen title. The
channels are HTML title, og:title and Article/NewsArticle JSON-LD headline; they
share a publisher response and are not independent corroboration. Article titles
are observed labels, not verification of their factual claims.

The final pages still declare og:url without /a/. None therefore gains strict
literal URL agreement merely because current routing was observed. Newly saved
publication metadata matches the prior dates (2021-03-17, 2026-10-06, 2014-10-26,
2017-11-20 in slot order); the under-water page still has zero h1 elements.
These observations do not repair the old date or heading failures.

## Verification and limits

**406/406 full-workspace tests** and **367/367 isolated-public-export tests**
pass; the same **39 archive-dependent tests** remain excluded from the public
runner. Eight new fixtures cover URL distinctions/rejections, relative redirects,
CONNECT/informational blocks, served aliases, missing/conflicting title and
canonical fields, inconsistent/non-publisher chains, HTTP/timeout failures,
request limits, one-attempt accounting and refusal to overwrite capture slots.

The [separate verifier](../scripts/verify_routing_v53.py) reconstructs the header
chains and metadata decisions without invoking the production assessor. It
checks telemetry, artifact hashes, exact commands/limits, timing, all four frozen
endpoint identities, retained readiness and all **52 prior runs and deliverable
seals**. It makes zero network requests. See the
[verification receipt](000053_verification.json). Both implementations use
BeautifulSoup html.parser; this is same-agent engineering verification, not
independent scientific review or browser visibility validation.

All four new final response bodies differ byte-for-byte from the original E50
captures. No historical body was replaced, and no cause of those differences was
inferred. Matching title/canonical fields establish only the registered current
route diagnostic. They neither prove unchanged article content nor authenticate
historical publication/routing behavior, historical bytes or the immediate
source of an FL passage. The earlier numeric results and scope ledgers are fixed.

This step computes no scaffold/alignment, numeric/uppercase or opaque lexical/
semantic scores. Current-alias support is separate from source-work identity,
source independence, untouched status, natural-benchmark admission and readiness.
Both intake capacity and the natural-benchmark capacity remain unmet.

Next bounded step: register a prospective **offline intake rule and capacity
decision** using the saved title/routing evidence and E52 uniform paragraph
scope. Apply the same rule to the reference and every intake slot, retain the
hard publication-date cutoff and all original outcomes, and report how many
captures qualify under that new rule. This should close the metadata/scope audit
sequence before any new acquisition or scaffold comparison. A rule that permits
agreeing metadata titles in place of h1 must be explicit and cannot be
backdated as an E50 success. No such admission or scoring was performed here.
