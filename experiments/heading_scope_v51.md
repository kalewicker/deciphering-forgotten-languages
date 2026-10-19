# Experiment 51: offline title representation and direct-paragraph scope audit

Question: where is the q01s01 title represented in the saved HTML, and what static
entry-content text is omitted by the frozen direct-p scope? The selected article
failed v50's h1 check. Preserve that failure, the one-ready/four-slot capacity
failure, all old scores and the ready q01s00 capture. This audit is diagnostic,
not a new eligibility rule, source-identity admission or structural scoring test.

Freeze protocol, config, code/tests, the exact selected nominee, raw body/receipt,
v50 observation/selection/report, v50 parser code, and all 50 old manifests/seals
before inspecting additional title/layout fields. Earlier exposure includes the
search result, native date, empty h1 inventory and old direct-p text. No new
acquisition, network request, browser rendering, CSS/JavaScript execution, OCR,
numeric/uppercase inventory, matching against FL quotations or scaffold scoring.

Use BeautifulSoup html.parser on saved bytes. Reproduce the v50 observation
exactly with its sealed inspector before new diagnostics. The original raw-body
hash, nominee URL, receipt/final URL and parsed body/direct-p spans are immutable.
No parser repair, title replacement or scope expansion in old evidence.

Fixed title inventory: every HTML title; og:title, twitter:title and name=title
meta value; every JSON-LD Article/NewsArticle/BlogPosting/ReportageNewsArticle
headline (walk nested objects/lists/@graph, record JSON errors without repairs);
every h1-h6; .entry-title, .post-title and [itemprop=headline] element; every body
alt/title/aria-label attribute; and every body element whose complete get_text
matches the expected service title. Retain all records, not a winning field.
Metadata title comparison strips only the frozen v50 final Physics World suffix,
then NFC/casefold/whitespace normalization. Record original strings and DOM tag
ordinals/ancestor names. Ordinals identify parsed DOM nodes, not raw byte spans.
Record exact case-sensitive expected-title occurrences in the reproduced body,
including all duplicate positions, with original Unicode spans. These occurrence
counts are title diagnostics, not quotation/opaque-language scores.

Record every canonical and og:url value against the original nominee resource
key and the receipt final URL. Copy the original publication/modification fields
and check their exact equality to v50. Metadata agreement is a descriptive flag:
at least two distinct nonempty title families among HTML title, og:title,
twitter:title and Article headline; every nonempty value in those families must
match the expected title; at least one canonical and one og:url must exist and
all identity URLs/final URL must match. Empty channels cannot count as agreement.
These fields share one publisher response and are not independent corroboration.
No h1 absence, DOM title match or other field may override a contradictory field.

After removing exactly script/style/noscript/template/svg/canvas as in v50,
inventory every nonempty NavigableString/CData leaf under the unique entry-content
container. Preserve original leaf text, stripped text, leaf order, parent DOM
ordinal and immediate container-child tag. A leaf is included iff it descends
from a direct p child; all other leaves are excluded under the old rule. Inline
emphasis/span text inside a direct p remains included; nested div>p is excluded.
Comments are not text leaves. Keep every direct paragraph, including empty ones,
and reproduce all old paragraph strings, body spans and mapping counts exactly.

Excluded text categories use ancestor priority: form (form/button/input/label),
table (table/thead/tbody/tr/td/th), figure (figure/figcaption), blockquote, list
(ul/ol/li), heading (h1-h6), then other. Do not choose a category based on source
meaning. Preserve each leaf/category and counts/stripped-character totals. The
ordered stripped leaves joined with spaces must exactly reproduce the full
container get_text; included leaves must reproduce the joined nonempty direct-p
text. Report full-container and direct-p strings/hashes locally and whether any
static container text is excluded. This accounting is not semantic coverage or
proof that all excluded material belongs in a future prose scope.

Tests before audit cover metadata agreement versus missing h1, conflicting/empty
title fields and URLs, Article-only JSON-LD with malformed scripts, split body
titles, direct versus nested paragraphs/inline leaves, excluded category priority,
comments/script removal and ambiguous paragraph mapping. After audit separately
reconstruct title/identity channels and leaf inclusion/accounting, verify original
observation hashes, all 50 old manifests/seals and unchanged readiness. Shared
HTML parser and same-agent verification are disclosed; no independent review.

The audit completes with all observations, including disagreement/unavailable
fields, preserved. It performs zero new structural, lexical or semantic scores;
no new candidate/readiness/source/meaning/test-unit admission is made. Natural-
benchmark and v50 capacity remain unmet; scientific acceptance/semantic metrics
null. Seal report/evidence, run local/public checks, checkpoint evidence locally,
commit/push appropriate public artifacts on main, and preserve publication scope.
