# Experiment 38: dated target recovered; immediate source relationship unresolved

The registered dated-material gate **passes**. A saved replay of the fixed ANITA
post is bound to the exact archive-index record at **2026-01-10 22:21:00 UTC**.
The original URL, timestamp, Memento header, title, single post-body and saved
decoded-body fingerprint agree. This supplies the missing dated target material;
it is not a current native-site observation, independent WARC authentication or
evidence that a cited paper supplies the post's opaque prose.

The scoped literal check finds **0/8 quoted spans** in the fixed source paper.
All eight engineered source-copy controls pass. The exact arXiv citation occurs
once in the saved post. Source relationship and whole-post coverage therefore
remain unresolved; no word meaning or translation is admitted.

## Fixed routes and capture

Only the registered exact-URL CDX query and its metadata-selected replay were
requested. Both return HTTP200 with complete saved bodies. There is no native
retry, alternate timestamp, search, mirror, replacement source or new paper
download. Both routes remain in the fixed denominator.

| Dated-material requirement | Result |
|---|---|
| Exact single CDX record at/before the frozen cutoff | Pass |
| Metadata and replay transport complete | 2/2 |
| Replay original/timestamp and post-body/title identity | Pass |
| Memento timestamp equals selected capture | 20260110222100 |
| Saved decoded replay SHA1/base32 equals CDX digest | XJHO5WZ7FAJACCPJK3NFGMLIWHRKA3X4 |
| Combined material gate | Pass |

The archive capture date is distinct from the post's 2018 publication date. The
saved material is the replay response, not an original WARC record. This time the
curl content-decoded body agrees with the index digest without an encoding-layer
repair. The earlier native TLS failures and v37 indexed-only limitations remain
unchanged in their original records.

The [gate ledger](../data/v38/dated_material_gate.json) retains every requirement,
the selected record, digest comparison and extraction details. Raw bytes and
headers remain in [acquisition](../data/v38/acquisition/). Normalization exports
one whole visible post-body, removes only script/style/noscript and joins visible
text with spaces: **8,766 Unicode code points**. This is a derivative with its
own coordinates, separate from raw HTML bytes and the older indexed line labels.
The fixed indexed fallback is not used for the primary observations because the
dated gate passes.

## Source representation and literal scope

The source is the unchanged eight-page arXiv hep-ph/0209057v1 PDF recovered in
v37, *Neutrino Radar*. All eight complete PDFium page images were inspected for
identity, order, legibility and extraction coverage. Pypdf page text remains
unmodified and page-local. Line-end hyphenation, broken word spacing, mathematical
typography and an apparent malformed reference on page8 remain visible; no
post-result text repair was made. This is source-representation inspection by
the same assistant, not independent scientific or passage review.

The quote rule retains every nonempty balanced ASCII/directional double-quoted
span in the selected target: seven longer quoted blocks and one expanded
instrument name. All eight have zero exact literal occurrences across the eight
source pages after NFC, casefold and whitespace collapse only. Every zero-page
comparison remains in the [observation ledger](../data/v38/observable_scope.json).
This is not an opaque-language alignment or translation test.

The first nonempty line of each source page is used as an engineered sensitivity
query, and all **8/8** hit their own page. The fixed absent-marker query hits no
page. These controls check the literal operation; they do not supply independent
natural positives, hard negatives, a real-world error rate or semantic labels.
No pages were concatenated across boundaries, dehyphenated or paraphrased.

The fixed exposed whole-token anchors show:

| Anchor | Target export | Source PDF extraction |
|---|---:|---:|
| ANITA | 17 | 0 |
| IceCube | 4 | 0 |
| Antarctic | 2 | 0 |
| neutrino | 18 | 34 |
| radar | 4 | 2 |
| 15717147 | 2 | 0 |

These descriptive counts include the post's prose, quotations, title and
bibliography. They are selected development observations, not independent clues
or a calibrated source-identity method. Shared topic vocabulary does not establish
opaque-word meanings. Absence of the other terms or exact quoted spans does not
reject translated, edited, substituted or partial reuse elsewhere in the post.

The exact citation URL occupies target code-point span **[8496,8533)** in the
export. That establishes the bibliographic link to this paper. It does not
establish an immediate passage relationship, and the zero literal-quote result
does not prove the paper was unused. Do not supply the paper's English prose as
a translation of the unknown text.

## Review materials and next evidence boundary

The [neutral review packet](../data/v38/neutral_review_packet.zip) is ready for a
scoped source-disclosed material review. It contains the unchanged PDF, dated
post text, original replay HTML, headers/index/route receipts, page-local source
text, material hashes and a blank reviewer declaration. It excludes our quotation
results, anchor counts, lexical predictions, proposed translations and preferred
alignment. Its [receipt](000038_neutral_packet_receipt.json) checks every ZIP
member and exact source/target bytes. It is a post-run handoff derivative of the
frozen evidence, not a new experiment or a completed review.

The separate [annotated bundle](../data/v38/scoped_materials.zip) preserves the
same-assistant observations and all gate outcomes for project inspection. A
reviewer exposed to it or this report must disclose that exposure; the neutral
packet cannot undo prior knowledge. Candidate source identity is disclosed in
both packets, so neither evaluates blinded source retrieval. No reviewer was
assigned, contacted or represented as independent.

Material readiness has improved. Independently reviewed parallel passage units,
new meanings and untouched test groups remain zero. The four-work capacity gate
and v36 source-absence failure remain unmet/failed respectively.

The next bounded diagnostic can use **the first other explicit versioned arXiv
identifier in this saved bibliography, 1809.09615v1**, to ask whether it supplies
any of these same quoted spans. Register that one source and one acquisition
route before downloading it; reuse the unchanged literal rule and all eight
queries, retain absence, and do not replace a failed source. This would test a
different nominated citation on exposed development material. Even a literal
English quotation match would not validate the opaque FL passages or create
independent semantic gold. Independent material review remains a separate route.

## Verification and execution note

All **329 tests pass**, including Unicode/casefold witness mapping, no silent
dehyphenation, indexed-parent lineage, complete quote retention, exact archive
identity/digest format and rejecting a Memento header found only on a redirect.
The registration, implementation and inputs were sealed before the two requests
and before whole-source comparison.

Offline verification independently reconstructs literal occurrence counts and
exact witnesses, quote/control/anchor denominators, capture-route accounting and
bundle integrity. It reextracts the source PDF using the same extraction library;
that shared component is explicit. All **37 prior run inventories and deliverable
seals** verify unchanged. The [verification receipt](000038_verification.json)
passes, without claiming independent scientific or semantic validation.

The initial source-export command failed before creating output because the
bundled PDF Python lacked BeautifulSoup on its import path. The [failure record](../data/v38/source_export_runtime_failure.json)
is preserved. Adding the already installed project's pure-Python dependencies
to PYTHONPATH resolved runtime setup; no code, source, target, acquisition route,
criterion or result changed, and no dependency was downloaded.

Scientific acceptance and semantic metrics remain null. Source-identity,
semantic-label, independent-review and untouched-test admissions, opaque-passage
scoring, lexical changes and external messages remain zero.

Artifacts: [registration](../experiments/dated_capture_scope_v38.md),
[preflight](../data/v38/preflight.json),
[target export](../data/v38/target_export.json),
[source export](../data/v38/source_export.json),
[visual inspection](../data/v38/visual_review.json),
[immutable report](../runs/000038_dated_capture_scope/report.json).

Offline verification uses the existing bundled PDF runtime and project parsing
dependencies, without new acquisition:

```sh
PYTHONPATH=src:.venv/lib/python3.14/site-packages /Users/kalewicker/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_dated_capture_scope_v38.py
```

Acquisition and exports refuse existing outputs; verification preserves its
successful receipt. Leave all original artifacts unchanged.
