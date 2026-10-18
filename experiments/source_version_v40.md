# Experiment 40: version and date provenance

Question: can two official records support a mechanism for the 2025 internal
date in the preserved PDF marked 1809.09615v1 / 25 Sep 2018?

This is a provenance diagnostic, not another quotation or language test. The
v38/v39 targets, queries, denominators, outcomes and original PDF remain fixed.
No historic byte identity is assumed from a version URL or visible margin.

Before requesting either route, freeze this registration, prior manifests and
deliverable seals, the v39 PDF and provenance notice, and acquisition/parser/test
code in a timestamped preflight receipt. Make exactly two initial HTTPS GETs,
sequentially: https://arxiv.org/abs/1809.09615v1 and
https://arxiv.org/src/1809.09615v1. Follow at most three HTTPS redirects per GET;
20 seconds total and 8 seconds connection timeout per route. Limits: metadata
4 MiB, source response 20 MiB. No retry, alternate endpoint, search, new PDF,
archive request, target recapture, compilation or external review contact.
Transport failures are unavailable evidence, not negative findings.

Preserve response bodies, headers, commands, times and hashes. From official
HTML preserve metadata tags, version links, submission history and visible text.
Require the actual saved page to identify the intended work/version before using
its history. Inspect the previously saved PDF metadata, without downloading it.
Dates in PDF metadata are self-reported fields, not authenticated creation times.

Read source in memory only: tar, gzip-tar or single TeX (optionally gzip).
64 MiB expanded limit, 1000 members, 4 MiB per regular member. Reject unsafe
paths, duplicate paths, links, devices, unsupported containers and expansion
limits; never extract paths or execute files. Preserve hashes of regular members
and decoded TeX with UTF-8, falling back explicitly to Latin-1. Inventory every
TeX file. Record exact Unicode spans and lines for non-comment date, today,
documentclass, begin-document and maketitle tokens. These are lexical witnesses;
manual surrounding-context inspection must distinguish live preamble declarations
from comments, macro definitions, conditionals or unused alternative files.

Report each component independently: official identity/version history, source
availability and title/version consistency, explicit fixed/dynamic date evidence,
and PDF metadata consistency. A live date-today declaration supports a render-time
date mechanism but does not demonstrate that this exact source generated the
preserved PDF or prove when it was rebuilt. Missing or ambiguous evidence stays
unresolved. Historical 2018 byte authentication remains false absent independently
dated bytes, which are outside this request budget. No quotation re-score,
semantic labels, source-identity admission or untouched natural test units.

Validate source reader against malicious/oversized and comment fixtures, verify
all saved witnesses/receipt hashes, preserve all 39 prior runs and deliverable
seals, and run the full existing test suite. Seal the report and findings.

Next action is determined from the result; do not automatically expand acquisition.
