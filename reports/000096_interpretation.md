# E96: the fixed source acquisition failed before wording could be tested

The single registered request to the catalog-offered Gutenberg plain-text URL
failed TLS certificate validation: the client reported a self-signed certificate
in the certificate chain. **No HTTP response and no source bytes were received.**
The attempt is closed as an acquisition failure. Page binding and wording comparison
were **not executed**; match counts are **null**, not zero out of 22.

This says nothing about the truth of the catalog claim, whether Gutenberg is
available in another environment, or whether its offered text preserves printed
pagination. The cause of the certificate-chain failure was not diagnosed. No
certificate bypass, alternate client, redirect, retry, mirror or edition search
was attempted.

## Fixed test and preserved failure

The [protocol](../experiments/burton_wording_v96.md) and
[registration](../experiments/burton_wording_v96.json) froze candidate 01's package
ordinals 2–23 as the proposed 22 prose renderings, excluding ordinal 1 as the
separately claimed heading. This ordinal assignment is a test hypothesis, not an
author-provided source-span map. Exact package English spans remain local.

The only source URL was the literal catalog-offered Gutenberg text ending in
`/cache/epub/57208/pg57208.txt`. Its request budget was one anonymous GET, no
redirects, 30-second socket/60-second overall timeout, and an 8 MiB body limit plus
one-byte oversize detection. The request intent preserved the acquisition-script
hash before the attempt. The source was not opened by any other tool.

The receipt retains the certificate error, null HTTP status, empty response headers
and a zero-byte body artifact. One client acquisition attempt is not a successful
HTTP transaction. No source decoding, edition inspection, page-marker inventory,
whole-book search or target-wording search occurred.

| Stage | Result |
|---|---|
| Frozen prose targets | 22, all retained |
| Client acquisition attempts / budget | 1 / 1 |
| HTTP responses / source bytes | 0 / 0 |
| Printed-page binding | Not executed |
| Literal and diagnostic wording counts | Null: not executed |
| Source/translation validation | None |

Had source intake succeeded, the fixed procedure would first require credible
boundaries for pages 252 through 257, binding pages 254–256 followed by 252–253.
It would stop if the representation could not establish those ranges, rather than
use target wording to locate favorable text anywhere in the book. That requirement
has not been tested or relaxed.

## Next resource boundary

Do not repeat this sealed attempt or disable certificate checks. A possible next
route is a user-downloaded copy of the **same offered plain-text representation**,
with its requested/final URL, download time and method recorded. Such a delivery
would require a new intake registration and would not repair E96. Its availability
and page-marker suitability are unknown. No further acquisition is pending here.
Do not substitute a different edition or broaden the search simply to obtain a
wording match.

The underlying source claim remains unresolved. Semantic benchmark capacity stays
0/4; there are no new untouched units, source identities, validated translations,
models or lexicon results.

## Verification

Read-only replay checks all registered hashes, registration-before-request timing,
acquisition-script identity, the single intent/receipt, the zero-byte body, all 22
package spans, and null downstream metrics. E95 sealed artifacts remain unchanged
and match the preceding local evidence checkpoint. Syntax, local links and diff
whitespace were checked. No model/comparator tests were rerun for this failed
acquisition; the earlier E94 counts remain historical, not new validation.

The exact offered URL, English targets and acquisition artifacts remain local-only.
Public main contains the protocol, acquisition recorder, verifier and aggregate
report. Replay, requiring local evidence:

```sh
.venv/bin/python scripts/verify_burton_wording_v96.py
```
