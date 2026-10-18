# Experiment 40: a supported date mechanism, historical bytes still unproven

The retrieved source requests a current date at rendering time. Together with
the preserved PDF's printed date and self-reported timestamps, this supports
a later rendering as the explanation for the 2018 version marker / 2025 internal
date. The actual build chain and original 2018 byte identity remain unproven.
This experiment adds provenance evidence, without revising experiment 39.

## Registered acquisition and observed evidence

The [registration](../experiments/source_version_v40.md), JSON inputs and code
were frozen in a timestamped [preflight](../data/v40/preflight.json) before
acquisition. Exactly two registered GETs completed, both HTTP 200, with no
redirects, retries, alternate routes or new PDF acquisition. Raw response
bodies, headers, commands, timestamps and hashes remain in
[the acquisition directory](../data/v40/acquisition).

| Component | Saved observation | Scope |
|---|---|---|
| [Official version page](https://arxiv.org/abs/1809.09615v1) | Explicit v1 title and URL; submission history lists v1 at 25 Sep 2018 17:56:31 UTC | Current official record of the submission, not a 2018 byte snapshot |
| [Official versioned source](https://arxiv.org/src/1809.09615v1) | gzip-tar, 160,836 response bytes; eight regular files, one TeX document | Currently served source, title and version route consistent |
| Main source, line 98 | `\date{\today}` | Supports a render-time date mechanism |
| Preserved v39 PDF | Printed `(Dated: March 7, 2025)`; CreationDate and ModDate both `D:20250307191020Z` | Self-reported fields agree with the printed day; timestamps are not authenticated build logs |
| Source HTTP header | Last-Modified: 8 Mar 2025 00:30:30 GMT | A response metadata observation; does not prove a content revision |

The main-source witness is [anita_evts.tex, decoded text](../data/v40/tex/member0004.txt),
Unicode half-open span **[5119, 5132)**, line **98**. The date command is
uncommented, at top level in the front matter, after `\begin{document}` and
before `\maketitle`. The title matches the official record. Inspection of
the first 113 source lines and bundled `aasdefs.sty` found no alternate date
assignment, relevant conditional or date/today redefinition. Only one TeX
entry point is present. Class and external package implementations were not
acquired or inspected, and no TeX was executed.

The registration's generic reference to a live preamble declaration is made
precise here: this REVTeX declaration is in front matter after begin-document.
The registered question and criteria were unchanged. The lexical scanner's
findings were checked in context rather than treated as execution proof.

The [context review](../data/v40/manual_review.json),
[source inventory](../data/v40/source_observations.json),
[metadata observations](../data/v40/metadata_observations.json) and
[PDF metadata](../data/v40/preserved_pdf_metadata.json) preserve these details.
Source response SHA-256:
`f7d4410eb61b03a36e7d9dd753196ab2daa13408e72bc92033c63ba2e7c9b19b`.
The v39 PDF remains unchanged:
`b86c606efa1947fa4e2fc7b084b1d9329b306fb9eb7fbf1d230f7ef590a1d267`.

## Interpretation and limits

**Supported inference:** rendering source that uses today's date can produce
a later internal date while retaining the submission version. The currently
served source and PDF are consistent with that mechanism and a March 2025
rendering. The evidence does not demonstrate that this exact source produced
this exact PDF, identify a service rebuild event, or establish a textual change
in 2025. No independently dated 2018 source/PDF bytes were acquired.

Historical-byte authentication remains **false**. The 2018 marker continues
to satisfy v39's originally registered visible-version gate. Its fixed result
remains **1/8 name-only literal matches, 0/7 longer blocks** for the preserved
PDF. Nothing was rescored. No opaque FL meanings, immediate source identities,
independent reviews or untouched test units were admitted; semantic metrics and
scientific acceptance remain null. Natural-benchmark capacity is still unmet.

## Validation and next step

**337/337 tests pass**, including four new source-reader tests for container
handling, unsafe paths/links, expansion limits and comment-aware witness offsets.
The separate [verification program](../scripts/verify_source_version_v40.py)
checks route accounting, preflight order, receipt hashes, raw member inventory,
title/version consistency, exact text witnesses and PDF fields. All **39 prior
runs and their deliverable seals remain intact**. The verifier was written
after acquisition and shares BeautifulSoup, pypdf, tarfile and gzip; this is
engineering cross-checking by the same agent, not independent scientific review.
See [verification receipt](000040_verification.json) and
[immutable run report](../runs/000040_source_version/report.json).

Stop this date-provenance branch here. Next, register a small quotation-origin
discovery test using the complete **quote00**, the lowest-ID long quotation
already frozen in v38. Fix one exact-phrase discovery request and retain its
full response, attribution and unavailable/no-lead outcome before any follow-up
capture. Any resulting lead concerns that English quotation; source identity
for opaque FL would still require separate evidence. No such search was made
in experiment 40.
