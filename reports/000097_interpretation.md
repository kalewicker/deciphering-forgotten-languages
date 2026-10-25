# E97: the supplied text identifies the work but cannot bind the required pages

The user-delivered file is **555,341 bytes**, preserved unchanged and successfully
decoded as strict UTF-8. Its header identifies the expected Burton work and editor,
with an 1898 Hutchinson imprint. However, the registered marker inventory finds
**zero candidates for each required boundary, 252–257**. Page binding is unresolved.
The **22-unit wording comparison was not executed**; its counts remain null.

This is a limitation of the supplied representation under the fixed locator rules,
not evidence against the source claim. No whole-book target search was performed.
No edition substitution, page inference from matching wording or threshold change
was made. E96 remains a separate failed network acquisition.

## Provenance and bounded inspection

The user supplied `pg57208.txt`, the exact previously offered Gutenberg URL, and
save time **1:12 pm PST**. Save date, browser, method and final address-bar URL were
not supplied and remain unknown. The reported URL is provenance, not authenticated
origin evidence. Preservation time records our copy, not the user's download.

The [new protocol](../experiments/burton_local_v97.md) and
[registration](../experiments/burton_local_v97.json) bound the delivered bytes and
unchanged E96 targets before decoding. The file is within the inherited 8 MiB
limit. Inspection was restricted to the first 10,000 Unicode code points for
metadata and a complete inventory of registered numeric-marker forms. No network,
rendering or source replacement occurred.

Five exact metadata spans retain the title, author, editor, publisher and imprint
year. They support header compatibility, not independent authentication of the
edition or proof that its pagination matches the catalog claim.

## Page-marker gate

The inventory recognizes bracketed/brace-delimited integers with optional
Pg/Page/p prefixes, and standalone integer lines. It records **443 candidate
markers** overall. These are numeric labels, not automatically page boundaries;
footnotes and other numbering must not be promoted to pagination.

| Required boundary | Candidate count |
|---|---:|
| 252 | 0 |
| 253 | 0 |
| 254 | 0 |
| 255 | 0 |
| 256 | 0 |
| 257 | 0 |

No required-boundary context windows exist to inspect. Therefore a credible unique
run cannot be established to delimit pages 254–256 followed by 252–253. This
finding is limited to the registered marker forms; it is not proof that every
possible pagination convention has been excluded.

The fixed target denominator remains all 22 package prose renderings, ordinals
2–23, with that mapping retained as a test hypothesis. No target words were loaded
into the intake scanner or searched in the source. Literal, whitespace-diagnostic
and ordered coverage metrics are all uncomputed, not observed zeros.

## Stop and useful next resource

E97 is complete and stopped. The downloaded text is preserved for provenance, but
it does not admit the page-specific test. Repeated text searches or additional
unpaginated downloads would not resolve this gate.

The next useful step, if this claim is pursued, is a separately registered check
of **one pagination-preserving representation of the same edition**, such as a
page-anchored transcription or scan with printed page numbers. Establish the exact
representation and a bounded retrieval route before looking for target wording;
then require the original page ranges rather than expanding them. Availability
of such a representation is untested. No alternative representation was opened,
requested or acquired in E97, and no new capture is needed from the user yet.

No English translation, opaque meaning, unique source identity or independent
review was validated. Semantic benchmark capacity remains 0/4. The positive native
text results from E93/E94 remain intact and separate from this source-location gap.

## Verification and publication

A separate read-only verifier reconstructs numeric-marker candidates without
importing the inventory script, checks all 443 spans, the six missing required
boundaries, the bounded header/evidence spans, registration hashes and null
comparison metrics. It was written after inspection and is a computational check,
not independent scholarly review. Original and preserved file bytes match; E96's
sealed artifacts remain unchanged and match the local evidence checkpoint.

Python syntax, local links, manifest hashes and whitespace checks passed. Model
and comparator suites were not rerun because no predictor/comparator changed and
no wording comparison ran. Earlier suite totals remain historical results.

Raw text, markers and metadata evidence remain local-only. Public main contains
protocol, intake/verifier code and aggregate reports. Read-only replay requires
the local archive:

```sh
.venv/bin/python scripts/verify_burton_local_v97.py
```
