# E98: fixed Gutenberg edition HTML pagination and conditional wording test

Preserve E96's failed request and E97's unpaginated-text result. New representation
route: one web-provider OPEN of the already documented Gutenberg catalog entry
https://www.gutenberg.org/ebooks/57208, followed by at most one direct HTTPS GET
of the catalog's Read Online HTML link for that same ebook ID. If multiple such
links exist, use the first in catalog order. No search query, alternative edition,
mirror, authentication, redirect follow, TLS bypass or retry. If no unique usable
same-ID Read Online link can be selected, stop unresolved. Provider tool calls and
native HTTP attempts are separately counted; internal provider requests are unknown.

Preserve the catalog tool result, exact selected URL/evidence and request intent
before acquisition. Use system curl with standard certificate verification,
60-second maximum, 20-second connect timeout, maximum 8 MiB, no redirects and
Accept-Encoding identity. Preserve headers, bytes and errors. A failed intake
stays failed. Do not switch back to E96's text request. The representation is new,
not a repaired E96 acquisition. Oversized, non-200, encoded or non-UTF8 HTML cannot
proceed. Preserve raw bytes without rendering scripts or fetching embedded assets.

Before wording search inspect only header/title/imprint metadata and the inventory
of explicit DOM page anchors/labels. Use BeautifulSoup/html.parser. Required page
anchors 252 through 257 must each occur exactly once, in ascending document order,
with printed numeric labels matching anchor suffixes and a coherent global
pagination sequence. Save exact DOM/string boundary evidence. Check the title,
Burton, Wilkins and 1898 imprint against E97's header. Provider summaries alone
cannot establish raw DOM boundaries. Incompatible edition or ambiguous/missing
pages means comparison not executed, counts null. Do not locate pages using target
words. No substitution of a different representation after results.

If admitted, freeze fixture-tested extraction/comparison code and raw input hashes
before loading the 22 target renderings for matching. Retain E96's proposed package
ordinals 2..23, with the heading excluded. Extract DOM text in document order,
omitting script/style/noscript/template and page-label text; preserve inline
adjacency and add newline boundaries at br, p/div/li/headings/blockquote/pre/tr.
Retain spans into the exact extracted string and the decoded HTML page elements.
Windows are page 254 start to 257 start, then 252 start to 254 start. No target
may cross their artificial junction. Entire physical ranges stay fixed, including
any notes within them. No target-driven trimming or paragraph relocation.

Compare every target literally and separately under Unicode whitespace collapse
only. Record every occurrence, per-window spans and greedy ordered nonoverlapping
coverage across the prescribed window order. A missing target does not advance the
cursor. No spelling, punctuation, accents, case, hyphenation or fuzzy repairs.
All 22 remain in the denominator. Report misses without later rescoring. This
assesses wording of package English, not opaque meanings, semantic accuracy or
unique source identity. No controls chosen after scores.

Stop after this one bounded source/edition/page check and conditionally admitted
comparison. No more sources, acquisition routes, models or semantic admission.
Exact sources, provider results, targets and ledgers stay local-only. Public main
contains protocols, code and aggregate findings. Semantic benchmark remains 0/4.
