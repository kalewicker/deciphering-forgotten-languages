# Experiment 42: quotation and publisher attribution confirmed in a native capture

The single registered request acquired the current
[Physics World article](https://physicsworld.com/a/mysterious-radio-signals-could-be-from-new-type-of-neutrino/)
with HTTP 200. Its saved visible page body contains the complete quote00 once.
The same paragraph names Gorham as speaker and follows the quotation with
the words “he says.” This confirms what the publisher currently displays;
original quotation provenance, a historical 2018 representation and opaque FL
meanings remain unverified.

## Registered scope and capture

The [registration](../experiments/native_quote_v42.md), frozen query, selected
URL, acquisition/parser/tests and prior evidence hashes were sealed before
the request. Exactly **1/1 native requests** completed, with no redirects,
retries, other queries, additional source requests or FL recapture. All other
quotation queries and opaque passages were left unscored.

The content-decoded HTML response is **115,847 bytes**, SHA-256
`614382b38bf6f19c08834f780cfe17c0b5969ffe0f7d19cebee77775105a96a0`.
The raw body, headers, command, times and transfer receipt remain in
[the local acquisition directory](../data/v42/acquisition/source).
Headers are preserved locally and are not published.

All eight representation checks pass: complete transfer, HTML markup, one body,
matching final URL, matching publisher identity URL, one expected h1, minimum
visible-text length and no registered challenge text. The export removes only
the six registered non-prose element types and joins visible body text with
spaces. It preserves navigation and other body material: this is a
**publisher-page body representation**, not a certified complete article.
See [page observations](../data/v42/page_observations.json).

## Exact witness and attribution

| Observation | Result |
|---|---|
| Visible page body | 12,072 Unicode characters |
| Complete quote00 occurrences | 1 |
| Enclosing body witness span | [6903, 7053), half-open Unicode offsets |
| Quotation paragraph | DOM p index 15, zero-based |
| Paragraph's body span | [6600, 7108) |
| Registered context window | p indices 14, 15 and 16 |
| Gorham named in the quotation paragraph | Yes |
| Quotation followed by he-says wording | Yes |

The enclosing token witness includes punctuation around the frozen 147-character
quotation. No query character, apostrophe or matching rule changed. The exact
text and offsets are saved in [visible_page.txt](../data/v42/visible_page.txt)
and the JSON observations. The context review is recorded in
[context_review.json](../data/v42/context_review.json). It is a textual reading
of this page, not authentication of an interview or the identity of its speaker.

Current HTML metadata reports publication at **2018-07-17T13:03:49+00:00** and
modification at **2020-05-21T13:05:53+00:00**. These are publisher metadata
statements from the captured 2026 response. No dated archival copy was requested;
neither original 2018 bytes nor a direction of copying is established.

The v41 indexed lead is now supported by native publisher bytes for this
quotation and its reported attribution. The v38/v39/v41 outcomes remain fixed.
No immediate source identity for the opaque FL text, semantic label, independent
review or untouched natural test unit is admitted. Semantic metrics and
scientific acceptance remain null. Natural-benchmark capacity remains unmet.

## Validation and next step

**340/340 full-workspace tests pass**, including three new checks for unavailable
versus absent outcomes, script-only false matches and fixed attribution-window
witnesses. An isolated public export passes **301/301** tests, with the same
39 archive-dependent tests explicitly excluded.

The [separate verifier](../scripts/verify_native_quote_v42.py) reconstructs
request accounting, gates, visible extraction, whole-quote counts and exact
context windows. It checks raw hashes and frozen inputs, and confirms all
**41 prior runs and deliverable seals** remain intact. The verifier was written
after acquisition and shares BeautifulSoup html.parser; this is same-agent
engineering verification, not independent scientific review. See
[verification receipt](000042_verification.json) and
[immutable run report](../runs/000042_native_quote/report.json).

Next bounded step: use these already captured bytes for a separately registered
check of **all eight original English quotation queries**, keeping their IDs,
denominators and v38 literal rule unchanged. Quote00 becomes a known positive
control; the other seven queries remain untested against this native page.
No new acquisition is needed for that step. Partial-reuse tests or opaque
passage alignment would require separate registrations.
