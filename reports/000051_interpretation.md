# Experiment 51: title is present; URL disagreement and omitted static text remain

The missing h1 does not mean the saved page lacks a title. The expected title
appears in an **h2**, HTML title, Open Graph title and Article JSON-LD headline.
Those three metadata title families agree. However, the registered metadata
agreement flag is **false**: canonical and og:url disagree on the URL path.
The direct-p scope also excludes substantive nested text, not only widgets.

This is an offline audit of the fixed q01s01 capture, *Looking at the sky from
under water*. Its old h1 failure, readiness false and experiment 50's **1/4
ready** outcome remain unchanged. No title fallback, URL alias, broader prose
scope or new scoring was admitted.

## Frozen representation and title evidence

The [registration](../experiments/heading_scope_v51.md), config, code/tests and
**97 input hashes** were frozen before inspecting additional title/layout
fields. The old exposure already included the search title, native date, empty
h1 inventory and direct-paragraph extraction. The sealed v50 inspector exactly
reproduced the old observation from the original saved raw bytes. Parsed body
text, publication/modification values, all 21 paragraph strings and body spans
are unchanged. There were **zero network requests and zero browser renders**.

The fixed inventory retained every declared title channel, including nonmatches,
empty/missing families, headings and body attributes. No winning channel was
selected after inspection. Metadata matching uses the frozen publisher-suffix
removal and NFC/casefold/whitespace rule, without other title repair.

| Title channel | Matching records | Interpretation |
|---|---:|---|
| HTML title | 1 | Expected title plus publisher suffix |
| Open Graph title | 1 | Expected title plus publisher suffix |
| Article JSON-LD headline | 1 | Expected title |
| Twitter title | 0 | No nonempty family present |
| h1 | 0 | Original failure reproduced |
| h2 | 1 | Expected title in static body markup |

There are **two exact body-title occurrences**, at Unicode spans **[2849,2884)**
and **[2955,2990)** in the unchanged parsed body. Three matching body-element
records represent nested h2/a/span wrappers around one heading; they are not
three independent title confirmations. No JSON-LD parse error occurred. DOM
ordinals in the local ledger identify parsed nodes, not raw byte offsets.

All title channels come from the same captured publisher response and are not
independent corroboration. Static text presence does not establish browser
visibility, CSS layout, JavaScript behavior or historical page contents.

## URL diagnostic remains false

The saved canonical URL is
`https://physicsworld.com/a/looking-at-the-sky-from-under-water/`.
It matches the nominee and final request URL. The saved Open Graph URL is
`https://physicsworld.com/looking-at-the-sky-from-under-water/`, **without /a/**.
It does not satisfy the frozen native-article identity rule.

Experiment 50 required at least one matching canonical/og:url value; its identity
check passed under that rule. The separately registered v51 diagnostic requires
both channel kinds and all values to match, so **identity_urls_agree** and the
combined **descriptive_metadata_agreement** are false, even though the title
strings agree. These are distinct declared checks; the old result is not edited.
No request was made to the alternate URL, and no legacy alias, redirect or
identity equivalence was assumed. The discrepancy remains unresolved.

## Direct-paragraph scope omits static content

All **68 nonempty text leaves** under the unique entry-content container were
partitioned in order: **39 included**, **29 excluded** by the old direct-p rule.
Inline text under a direct p stays included; text in nested div>p does not.
Every direct paragraph is preserved, and all included leaves exactly reproduce
the old joined paragraph text. All leaves exactly reproduce full container text.

| Excluded structural category | Text leaves | Stripped leaf characters |
|---|---:|---:|
| Figure / caption | 7 | 1311 |
| Form | 9 | 346 |
| Heading | 4 | 123 |
| Other, including nested prose | 9 | 3374 |
| **Total** | **29** | **5154** |

The other category includes nested introductory material and **three nested
paragraphs in a later section**, not merely surrounding navigation. Captions,
section headings and a registration form are separately accounted for. The
form's instructions and contact text are source content, not actions performed
by this project. No form submission, script execution or access-control
interaction occurred.

Joined full-container text has **18,396 characters**, versus **13,213** in the
joined direct-p scope. The latter is the old 13,193 summed paragraph characters
plus 20 inter-paragraph spaces; this is not a changed extraction. The 5183-
character difference includes 5154 stripped excluded-leaf characters plus join
separators. These are representation counts, not semantic coverage or accuracy.

The direct-p scope therefore does not contain all static container text. That
does not imply all excluded material belongs in a future prose scope: form text,
captions, nested prose and headings need explicit treatment under a new uniform
rule. The [local audit ledger](../data/v51/audit.json) retains every leaf, parent
DOM ordinal, owner tag, category, original text and inclusion decision.

## Verification, limits and next step

**390/390 full-workspace tests** and **351/351 isolated-public-export tests**
pass; the same 39 archive-dependent tests are excluded publicly. Eight new
fixtures cover title agreement without h1, contradictory/empty title or identity
fields, Article-only JSON-LD/malformed scripts, split/repeated body titles,
direct versus nested/inline paragraphs, exhaustive category priority, comments/
script removal and ambiguous paragraph mappings.

The [separate verifier](../scripts/verify_heading_scope_v51.py) reconstructs all
title, URL and JSON-LD records, every text leaf/category and all accounting. It
checks exact preservation of the old body, paragraph spans and readiness, plus
all **50 prior manifests and deliverable seals**. It shares BeautifulSoup
html.parser; same-agent engineering verification does not independently certify
browser layout, source identity or scientific meaning. See the
[verification receipt](000051_verification.json) and local
[immutable report](../runs/000051_heading_scope/report.json).

The metadata/URL diagnostic remains false and the old intake capacity remains
unmet. q01s00 stays the one previously ready candidate; q01s01 gains no readiness
admission. No new scaffold/alignment, opaque lexical or semantic scores were
computed. No meanings, immediate source identities, independent reviews or
untouched natural units are admitted. All old scores and failed gates remain
fixed; scientific acceptance and semantic metrics remain null.

Next bounded step: preregister a **uniform structural-scope audit across all
five saved publisher pages** (the v42 page and all four v50 captures). Inventory
direct/nested prose, captions, headings and forms under the same prospective
rules before any further anchor scoring. Retain old scopes/scores and all date/
title failures; keep the canonical/og:url discrepancy explicit. Testing a
versioned extraction rule across the full captured cohort can address the
scope weakness without defining a one-page rescue or rewriting historical
admissions. No new acquisition or cohort scoring is part of this experiment.
