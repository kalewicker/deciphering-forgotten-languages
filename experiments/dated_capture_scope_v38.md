# Experiment 38: fixed dated capture and citation-scope audit

Register before new requests or whole-PDF text comparison. Target remains v37
post00, `2018/10/what-was-what-anita-really-saw.html`; source remains the exact
saved arXiv hep-ph/0209057v1 PDF. No replacement post, paper, edition or source
window. No natural alignment, lexical induction or semantic scoring.

## Two fixed route slots

Make one certificate-verifying HTTPS CDX request for the exact target URL, latest
HTTP200 text/html record at or before this registration's UTC cutoff. Fields:
timestamp, original, statuscode, mimetype, digest; exact URL matching; limit=-1.
Accept exactly one well-formed record with the correct original and cutoff.
If available, make one `https://web.archive.org/web/{timestamp}id_/{original}`
request. Otherwise preserve a skipped replay slot and reason. Timeout20 seconds,
connect8 seconds, maximum3 HTTPS redirects, 4MiB per response, no retries, native
site request, alternate timestamp, search or endpoint. Both route slots and every
failure stay in the denominator. A genuine infrastructure permission failure may
receive an explicitly recorded outside-sandbox diagnostic; scientific routes
and original failed artifacts are not overwritten.

Save raw response bytes, headers, effective URL, timestamps, errors and hashes.
Requests use the existing v23 curl procedure with content decoding; receipts
must state that representation. Compute the decoded replay SHA1/base32 as a
representation diagnostic against the CDX digest. A mismatch is not repaired by
guessing an encoding layer or claiming WARC authentication.

The dated-material gate requires complete metadata/replay transport; exact CDX
original and timestamp; effective replay original/timestamp; matching HTTP
Memento-Datetime; exactly one nonempty post-body; expected post title and a
canonical/original permalink; no challenge signatures; and agreement between
the CDX digest and the saved decoded body. This deliberately conservative gate
may fail because the CDX digest addresses a different encoding representation.
Preserve that failure. An available but failed-gate response is not promoted to
an authenticated dated post. No current native-post claim follows from an archive.

## Source representation and observable citation scope

Reuse all eight pages of the saved PDF. Export unmodified pypdf page text,
explicit page-local Unicode offsets and page images with PDFium. Visually inspect
complete page images for identity, legibility, page order, text coverage and
obvious extraction artifacts. No post-result repair of PDF word splits,
hyphenation, math, Greek symbols or OCR. Exact text absence has this extraction
limit. Same-assistant PDF review is engineering inspection, not independent
source/passages or semantic acceptance.

If the dated-material gate passes, audit the normalized saved post-body. If it
fails, separately audit only the already exposed v37 indexed representation:
reported lines28..88 (prose/title28..59, bibliography63..88). Strip only browser
line labels and wrapper/citation markup; retain links to the exact parent file
and source-character spans. These exposed boundaries are fixed before scoring.
Indexed material cannot satisfy the dated gate or prove full-post coverage.

Extract every nonempty balanced ASCII double-quoted or directional-double-quoted
span in that fixed representation; keep every span and raw offset, without
language filtering or selecting successful quotations. Assess exact literal
presence within each source page after NFC/casefold and whitespace collapse
only. Do not concatenate across pages, dehyphenate or paraphrase. Save all
page hits, including zero, and all source/query character witnesses. Such an
exact quote hit establishes only literal text reuse, not an opaque FL meaning.
Absence cannot reject translation, edited reuse or source material outside the
fixed representation. The query/source language and annotation status remain
unresolved.

As extraction sensitivity controls, use the first nonempty extracted line of
each source page as an engineered literal query; retain all eight and require
that each hits its own page. The fixed marker
`flv38literalabsencecontrol20261018` must return no page. These controls verify
substring sensitivity only and are not independent positive/negative sources.

Count the exposed, preselected whole-token anchors ANITA, IceCube, Antarctic,
neutrino, radar and 15717147 in the selected target representation and each PDF
page. These are descriptive text observations, not a scored alignment method,
rarity estimate, source-identity gate or proposed word glosses. Inspect the saved
bibliography for the exact arXiv URL/citation location. Distinguish a bibliographic
citation from evidence that the paper supplies an immediate passage or full post.

## Decisions and stopping

Report dated capture readiness separately from PDF representation readiness and
the observable quote/anchor ledger. All quote denominators, missing material,
failed digest/transport gates and editorial artifacts remain visible. Do not
silently substitute indexed text for raw material or broaden the source set.
No quote-match threshold admits source identity, semantic meaning or translation.

Prepare a new scoped material-review bundle if useful, preserving the original
v37 bundle. Label indexed-only material and same-assistant observations explicitly;
leave reviewer identity, independence, passage relationship and coverage fields
unfilled/uncertain. Do not manufacture a review or contact anyone. Four-work
benchmark capacity remains unmet, with zero independent-review, semantic-label,
source-identity and untouched-test admissions. Scientific acceptance/semantic
metrics stay null. Stop at the fixed routes and observed evidence boundary.

Hash-seal registration, code and inputs before acquisition. Verify route accounting,
bytes, exact text witnesses, fixed quote/control/anchor denominators and all 37
prior runs/seals offline. Separate algorithmic checks by the same assistant are
not external scientific review.
