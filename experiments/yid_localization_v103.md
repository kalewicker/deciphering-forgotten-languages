# E103 tests bounded passage localization on one Yid catalog lead

Select exactly one lead before inspecting its paired text or obtaining the
source. Use the lowest catalog ordinal among the 28 E102 rows whose only failure
is the numeric passage and wording criterion. Use the first usable HTTPS
locator in that row's single external claim, in catalog order. Usable means an
absolute URL with a hostname, no user information and no fragment. Keep the
recorded component reserved from pairing-rule development. The lead selection
uses metadata and cannot be changed based on source availability or localization.

Acquire the named representation once with a single verified HTTPS GET, no
redirect following, 30-second timeout and a 16 MiB response limit. Archive
intent, headers, bytes and outcome. Retain failures as data. Supply no alternate
edition, mirror or post in this study. Freeze the request and selected edition
claim before intake. A source may be a UTF-8 plain text, UTF-8 HTML or searchable
PDF. For HTML use BeautifulSoup with the Python HTML parser, drop script, style,
template and noscript and preserve text-node order with one separating space.
For a searchable PDF use the installed pdftotext with UTF-8 output and retain
form-feed page boundaries. No OCR. Require compatible title and author or an
equivalent edition identifier in the acquired representation before matching.
Record the identity check and extraction scope. The search scope is the entire
single acquired representation within the registered byte limit. Establish that
scope before exposing the package English to the locator.

If admitted, use every English field from the selected post's paired blocks,
including headings present in the ledger, as the denominator. Search only the
frozen extracted text. First report full-string occurrences after Unicode
whitespace collapse. Separately report exact consecutive sequences of
case-folded Unicode letter runs, with punctuation and nonletters as delimiters,
for queries of at least eight letter tokens. Preserve occurrence counts and
offsets in their corresponding views. The token view discards punctuation,
case and digits. Label duplicate or unscored occurrences explicitly. Do not
perform fuzzy search or choose favorable passages by apparent quality. Account
for the ordering and overlap of unique token spans in package order. Whole-source
search leaves section-level uniqueness and coincidental matches as limitations.

The feasibility criterion is at least 22 unique, mutually nonoverlapping token
spans and at least 80% of all paired blocks with a unique token span. Report
strict whitespace matches separately. A result meeting the criterion supports
a later fixed passage and native-text adjudication. It supplies no accepted
pairings or excerpt boundaries. A failed acquisition or identity gate leaves
the localization comparison unexecuted. A measured shortfall closes this
attempt. End after the single lead's disposition and verification. No Yid
pairing scores, model changes or semantic admissions are part of this study.
