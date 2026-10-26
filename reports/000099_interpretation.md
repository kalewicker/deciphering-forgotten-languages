# E99: all 22 English renderings occur in the claimed page order under whitespace collapse

The corrected extractor and a separate replay agree on the complete source text,
page offsets and both fixed windows. The single 22-target comparison produces:

| Registered view | Targets with an occurrence | Ordered nonoverlapping coverage |
|---|---:|---:|
| Literal extracted text | 0/22 | 0/22 |
| Whitespace-collapse diagnostic | 22/22 | 22/22 |

Each diagnostic match occurs exactly once across the two windows. The first **18**
renderings occur in printed pages **254–256**, and the remaining **4** in pages
**252–253**, in package order. These are package ordinals 2–19 and 20–23; the
separately claimed heading, ordinal 1, was excluded prospectively.

This supports the catalog's English-wording and page-order claim for all 22 prose
renderings under the declared whitespace normalization. It does not validate
opaque-language translations, unique source identity, direction of copying or
independent semantic accuracy. Literal failure remains a reported result; the
successful diagnostic does not replace it. No punctuation, spelling, case or
accent repairs were made.

## Correcting E98 without rewriting it

The [development protocol](../experiments/burton_extract_v99.md) and input hashes
were registered before new structural inspection. E98's frozen implementation and
failed run remain unchanged. The saved HTML was reused; no network or additional
source acquisition occurred. E96/E97's earlier limitations remain historical facts.

Inspection clarified E98's multiple-anchor containers: anchors 2, 130, 286 and 288
are unlabelled and immediately precede the next labelled anchor in a shared span.
That does not establish separate printed labels or malformed nesting. Four Roman
front-matter anchors are also unlabelled. All eight remain explicitly recorded;
none is promoted to a verified printed boundary.

The [developed rules](../experiments/burton_extract_v99_rules.md) associate each
anchor with only its own adjacent label and suppress only those label characters.
Surrounding prose, whitespace and nested contents are retained. Wrong labels are
rejected; missing labels remain explicit. All six required boundaries 252–257
have their own matching labels, are unique, and occur in the observed numeric
anchor sequence 1..351. Unlabelled anchors outside those windows do not define the
tested ranges. This development decision preceded every target-wording result.

Eight synthetic fixtures cover the observed shared-container failure, a genuinely
nested synthetic container, inline prose, Roman labels, wrong/missing labels,
unrelated label-like text, hidden content and unchanged match restrictions.
Production and separate stack-traversal extraction agreed during development
without loading target renderings for matching.

## Freeze, windows and one scoring attempt

The [execution registration](../experiments/burton_extract_v99.json) binds the new
code, rules, tests, replay and exact prior inputs. After freezing, the runner again
required agreement on the full extracted string, every anchor offset and both
windows. It saved the extraction and a timestamped verification receipt **before**
loading the 22 target renderings into the scoring stage.

The fixed windows contain **4,305** extracted characters for pages 254–256 and
**2,917** for pages 252–253. They are kept separate, in the claimed jump order.
No target can match across their artificial junction. E98's `matches` function is
reused unchanged. Greedy order, nonoverlap and missing-target cursor behavior are
unchanged; all 22 units remain in both denominators.

The literal view retains extracted line/whitespace structure and yields no full
rendering occurrences. Collapsing Unicode whitespace runs to ASCII spaces and
stripping boundary whitespace on both source and targets yields all 22 unique,
ordered occurrences. The result therefore establishes equality under precisely
that view; it is not a byte-identical or unnormalized quotation claim. Exact and
diagnostic occurrence offsets remain in their explicitly separate coordinate
systems, with fixed-window offsets into the full extracted source preserved.

## What is established, and what is not

The proposed ordinal mapping (all package pairs after the heading) was a declared
test hypothesis, not an existing catalog-provided alignment. Its 22 English
renderings now have unique whitespace-normalized occurrences within the specified
page ranges and order. Combined with E93's native-save correspondence, this gives
a traceable development example with both sides accounted for at the text level.
It still does not show that the English conveys the meanings of the opaque lines.

The catalog also describes continuous excerpts. Ordered matches alone do not
establish continuity: this experiment did not quantify intervening or skipped
source text. It also did not test alternative sources, wrong pairings, lexical
uniqueness or semantic interpretation. No independent review occurred. Semantic
benchmark capacity remains **0/4**, with zero untouched confirmation units.

E99 is complete and stopped. The next justified bounded question is whether the
saved match spans support the stronger continuity claim: account for every gap
between consecutive matches within each fixed source window, retaining omitted
material and the explicit page-range jump. Use the saved spans without changing
normalization, widening pages or rescoring targets. That audit is not launched
here. Translation/lexicon induction and new models remain premature.

## Verification and publication

The frozen replay implementation imports no production extractor and uses a
separate stack traversal and label check. Read-only metric verification reconstructs
occurrences with escaped regular expressions and checks ordering, all denominators,
window receipts and hashes. Both paths share BeautifulSoup/html.parser and the
written specification; this is computational corroboration, not independent
scholarly review. No code was changed after scoring.

**689 workspace tests and 650 isolated-public tests passed**, with the established
39 archive-dependent exclusions. All E98 sealed artifacts remain unchanged and
match the preceding local evidence checkpoint. Raw HTML, development exposure,
extracted windows, targets and exact spans remain local-only. Public main contains
code, protocols, tests and aggregate reports. Replay requires the archive:

```sh
.venv/bin/python scripts/verify_burton_extract_v99.py
```
