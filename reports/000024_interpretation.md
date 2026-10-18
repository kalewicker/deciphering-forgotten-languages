# Experiment 24: review-window equivalence and archive encoding layer established

The provenance continuation resolves two specific issues from experiment 23. Western's saved and newly downloaded PDFs agree exactly within the fixed five-page review window. Risk's preserved gzip entity matches the frozen archive index digest, and its decompressed HTML exactly reproduces the earlier captured body. Both native-site requests still fail TLS using the second certificate-verifying client. No translation, source correspondence or semantic label is accepted.

The registration and input/code preflight seal preceded all new comparisons and requests. The three fixed routes were attempted once each, with no redirects, retries, new archive timestamps or publisher downloads. Failed native attempts remain in the denominator. The result is **0/2 current native materials**, one successfully diagnosed dated archive response, and a passing five-page equivalence gate. Historical archived material remains available for review, separate from current-site observations.

| Check | Registered result | Practical meaning |
|---|---|---|
| Western old/new PDF pages 90–94 | 5/5 exact text, dimensions and RGB pixel matches; decoded content streams also match | Export the current window for independent review under a scoped equivalence supplement |
| Western entire PDF | Both 357 pages; raw hashes differ; whole-book extracted text differs | No whole-book or exact-byte equivalence claim |
| Risk fixed 20260312080026 archive replay | HTTP 200; title, body, original permalink, exact replay URL and Memento date pass | Same dated post material, with encoding-layer accounting now explicit |
| Risk encoded versus decoded fingerprints | Encoded gzip entity matches the frozen CDX digest; decoded bytes match experiment 23 | Earlier mismatch is explained by comparing different content-encoding layers |
| Two native permalinks using Python/OpenSSL | Both fail before HTTP with SSL RECORD_LAYER_FAILURE | Failure persists with this second secure client; root cause remains unconfirmed |

## Western source scope

The old PDF SHA-256 remains `053d0052282bfe3f785a5e5942b67d3a10524e170a6aa23506f7554ce4f0568f`; the new PDF remains `3b32dbbef37a301c93a2937c4d98f5e7319080eb34c7c19064198b46e55e401a`. These raw bytes are different. Both metadata producers are OpenPDF 1.4.2; creation dates differ. Because whole-document extracted text also differs, it would be incorrect to describe the change as metadata-only. Unrendered page differences have not been characterized, and no edition-change claim is made.

The preregistered gate requires every selected page to have nonempty identical pypdf-extracted text, equal dimensions and identical RGB arrays rendered in the same PDFium runtime at scale 1.5, with equal total page counts. All five pages pass; decoded page content streams also agree. Independent verification regenerates the text and pixels from both source PDFs and checks the saved image/text artifacts. Same-assistant visual inspection covers all ten complete old/new images: prose, headings, printed labels 65–69 and footnotes remain legible. The first and last selected pages visibly continue beyond the window; whole-FL-post source coverage and passage boundaries remain unverified.

The new [Western supplement](../data/v24/review_supplements/western_esoterism/review.md) exports text directly from the new PDF's fixed pages, preserving page labels, footnotes and extraction artifacts. It does not reuse an old normalized selection under a false current-byte binding. The original experiment-23 source-byte failure and 1/2 material-readiness result are unchanged. This new window-equivalence finding is a separate, narrower basis for independent review.

## Risk representation diagnosis

The fixed replay request used `Accept-Encoding: identity`, but the archive response declared `Content-Encoding: gzip`. Python preserved the received entity bytes after transfer decoding, before content decoding. The response's exact replay timestamp and Memento date agree with the March 12, 2026 record. There were no new CDX queries or alternative timestamps.

| Representation | Bytes | SHA-1/base32 |
|---|---:|---|
| Received gzip entity | 667,822 | `AYNW6DCPXX6R2FDHKH3NPQHGKJFEXMWH` |
| Frozen experiment-23 CDX digest | — | `AYNW6DCPXX6R2FDHKH3NPQHGKJFEXMWH` |
| Decompressed HTML | 1,104,875 | `CJWRTXXINGOBGMJOCQZQP3OEZK77W276` |
| Experiment-23 content-decoded HTML | 1,104,875 | `CJWRTXXINGOBGMJOCQZQP3OEZK77W276` |

Decompressed HTML SHA-256 is `95ffca82923711d9b18e767ea38e1c638142f58e26401b192c33de08f21d12eb`, exactly the earlier body hash; direct byte equality and whole-post extracted-text equality also pass. The registered encoding-layer explanation is supported for this captured response. The original discrepancy receipt is retained, with its historical statement of uncertainty; no favorable response replaces it. No original WARC record was fetched or independently authenticated, and fingerprint agreement does not establish an FL-to-publisher correspondence or word meaning.

The [Risk supplement](../data/v24/review_supplements/risk_math/review.md) retains the dated archived post and blank reviewer fields. Its publisher PDF remains the unchanged experiment-23 source. All three raw route receipts and both entity/decoded archive representations are retained in the [acquisition directory](../data/v24/acquisition) and [analysis directory](../data/v24/analysis).

## Native transport and stopping boundary

The project Python client uses OpenSSL 3.5.5, standard certificate and hostname verification, and the default trust store containing 128 CA certificates. It uses an explicit empty proxy handler, sends no credentials/cookies and performs no automatic retry. Both registered native permalinks fail with `URLError: [SSL: RECORD_LAYER_FAILURE]`. Experiment 23's curl failures and these OpenSSL failures are distinct preserved procedures; the root cause is unresolved, and universal inaccessibility is not established. The archive route succeeds with the same Python client. No further native retries belong to this experiment.

All seven new transport/representation/gate tests and the existing suite pass: **185 tests total**. Offline independent replay passes the request accounting, secure client settings, content-decoding bounds, HTML/date gates, both fingerprint layers, exact PDF window, neutral exports and blank review forms. It validates the input/code/output/artifact inventories of all 23 prior experiments and the experiment-23 deliverable seal.

The first verifier attempt failed on an engineering compatibility error: experiment 1 keys input hashes by document ID and hashes normalized text, while the initial verifier treated every key as a file path. The [failed audit receipt](000024_verification_initial_failure.json), original verifier and preflight seal remain unchanged. A separately [registered audit revision](../experiments/kamri_provenance_v24_audit_revision1.md) uses the established historical schema-aware hash checker, including early artifact_hashes. All experiment-24 gates are identical. The [successful verification receipt](000024_verification.json) binds the revision and failure; no capture, criterion or experiment result was rerun or overwritten.

Independent semantic reviews completed, semantic labels and untouched-test admissions remain **zero**; evaluation metrics remain **null/unavailable**. The same assistant's visual checks and offline independent implementation are engineering checks, not an independent semantic reviewer. Existing connected groups remain exposed development evidence. No dictionary, alignment/gap score or translation model executed.

The next bounded step is independent source/passage review of the two existing dossiers with these supplements. A reviewer must declare independence, check language scope and source coverage, record boundaries/correspondences/counterexamples and preserve uncertainty. Whole-post coverage is not yet established by either fixed publisher window. Until review is returned, lexical acceptance remains blocked. Any actual held-out validation additionally requires new, unexposed connected source works and frozen predictions; these two dossiers cannot supply an untouched fold. Further native access diagnosis, if warranted later, needs a new hypothesis and registration rather than repeated client switching.

Protocol references used to scope the procedure: the [Internet Archive CDX documentation](https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md) documents exact-URL index records and exposed fields; Python documents [urllib.request](https://docs.python.org/3.14/library/urllib.request.html) client handling and [ssl.create_default_context](https://docs.python.org/3.14/library/ssl.html#ssl.create_default_context) secure defaults. The encoding explanation above follows measured local byte/digest comparisons, not a generic promise that replay equals WARC bytes.

Artifacts: [registration](../experiments/kamri_provenance_v24.md), [machine-readable plan](../experiments/kamri_provenance_v24.json), [preflight seal](../data/v24/preflight.json), [PDF comparison](../data/v24/pdf_comparison.json), [visual review](../data/v24/visual_review.json), [immutable report](../runs/000024_kamri_provenance/report.json), [manifest](../runs/000024_kamri_provenance/manifest.json), [audit revision registration](../experiments/kamri_provenance_v24_audit_revision1.json), and [verification](000024_verification.json).

Reproduce offline with `.venv/bin/python scripts/verify_provenance_v24_revision1.py`; run tests with `.venv/bin/python -m unittest discover -s tests -q`. Do not rerun the acquisition or PDF-inspection scripts: they refuse existing evidence directories. The original verifier is retained as a failed audit artifact; use revision 1 for verification.
