# E99: anchor-local extraction correction and unchanged wording test

Preserve E98's sealed code, failed run and acquired HTML. No network or new source.
Use the exact saved HTML SHA-256 bound in E98, and E96's unchanged 22 targets
(package ordinals 2..23). Page windows remain 254–256 then 252–253, excluding the
heading. No target-driven source selection or normalization changes.

## Development before scoring

Register this scope and inputs before inspecting structure for the correction.
Inspect only page-anchor/label node structure at the four known nested pairs
(2/3,130/131,286/287,288/289) and required boundaries 252..257. Do not load target
English into development inspection or print source passages. Save structural
exposure records (node types, anchor IDs and labels), not an inferred source map.

Replace E98's whole-pagenum-subtree deletion with anchor-local label suppression:
associate each Page_* anchor with its own adjacent printed label; retain all
surrounding and nested prose. Numeric page labels must equal their anchor suffix;
Roman front-matter labels must likewise agree if encountered. Only the explicit
label characters are suppressed, with all other text preserved. Reject unknown
or ambiguous label associations rather than dropping a containing subtree.
Keep E98's script/style/noscript/template exclusions, inline adjacency, br and
block-boundary newline rules. No punctuation, spelling, case or accent repairs.

Develop synthetic fixtures for nested containers, multiple page anchors in one
container, inline prose surrounding labels, wrong/missing labels and boundaries.
Validate the correction against the saved document's complete 1..351 numeric page
sequence without inspecting target match outcomes. Freeze code, tests, independent
replay and exact input hashes before extracting final windows for the test.

Require extraction agreement with a separate traversal implementation on the exact
full string, numeric anchor offsets and both windows before loading the targets
for matching. Save a window-verification receipt. Only then run one literal and
one whitespace-collapse diagnostic through E98's unchanged matches function. Keep
all 22 units and all failures. No match may cross the artificial window junction;
greedy ordering and missing-target cursor behavior remain unchanged. Save exact
and diagnostic offsets. No code changes or rerun after scores.

## Stop and interpretation

Stop after this one extraction/window verification and conditionally admitted
comparison. Missing page support or replay disagreement prevents scoring; record
null counts. Scoring misses are observed misses, not authorization to repair
punctuation or expand windows. No whole-book target search, sources, controls,
models, lexicon work or independent semantic admission. A wording match would
support correspondence of package English to the cited edition's limited ranges,
not opaque meanings, direction of copying or unique source identity. Semantic
capacity stays 0/4; no untouched units are created. Raw sources, targets, structure
ledgers and exact comparisons remain local-only; publish aggregate findings.
