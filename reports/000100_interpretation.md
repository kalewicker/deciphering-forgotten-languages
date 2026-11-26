# E100 finds continuous English excerpts within both cited page windows

All **20 gaps between consecutive renderings within the two E99 windows contain
only whitespace**. The 18 renderings on pages 254–256 form one continuous excerpt,
and the four on pages 252–253 form another. The transition from package ordinal
19 to 20 is the declared backward page jump.

| Source window in package order | Renderings | Internal gaps | Whitespace characters in gaps | Gaps containing non-whitespace |
|---|---:|---:|---:|---:|
| Pages 254–256 | 18 | 17 | 23 | 0 |
| Pages 252–253 | 4 | 3 | 4 | 0 |

The result supports the catalog's stronger continuity claim for the package's
English wording. E99 found 0/22 full-span literal occurrences and 22/22 under
whitespace collapse. E100 starts from the 22 saved ordered occurrences and checks
the exact extracted gaps between them. Its scope is the saved Burton transcription.
The opaque-language meanings, direction of copying and immediate source identity
remain unresolved. Semantic benchmark capacity remains 0/4.

Each excerpt occupies part of its source window. The first window has 421 extracted
characters before its first match and 1,502 after its last. The second has 1,093 before
and 1,183 after. Those four edge spans are recorded separately from the 20 internal
gaps. The ledger accounts for all 21 consecutive package transitions and partitions
both windows into matched spans, internal gaps and edges.

The [protocol](../experiments/burton_continuity_v100.md) fixes the denominator and
strict criterion before measurement. A single non-whitespace character, including
punctuation, would count against continuity. The audit maps the frozen normalized
offsets back to the original extracted strings. A separate character scan verified
the mapping, exact slices, classifications and full-window partitions. All 21
sealed E99 artifacts match their hashes and the preceding local checkpoint. The
audit made zero new wording searches or source requests.

The exact source and gap ledger remain local. Run the read-only verifier with
`.venv/bin/python scripts/verify_burton_continuity_v100.py` against that archive.
