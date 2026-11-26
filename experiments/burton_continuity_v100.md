# E100 audits continuity within the two saved Burton excerpts

Use the frozen E99 extraction and whitespace-collapse occurrences for all 22
package ordinals 2–23. Require one saved occurrence per target, equal to its
saved ordered occurrence. Require the registered window order and observed split
of 18 targets on printed pages 254–256 and four on pages 252–253. Measure only the
saved span boundaries. E99's literal result remains a separate measurement.

Audit all 21 consecutive package transitions. Twenty are within a source window
(17 in the first, three in the second). The other transition is the declared
backward page jump. Record it without assigning a continuous source gap. Also
account for the four edge spans before the first and after the last match in
each window. Edges describe material outside the excerpt runs and are outside
the internal continuity denominator.

Reproduce the saved whitespace view with a Unicode code-point map back to the
exact E99 window. Each collapsed space maps to its full source whitespace run.
Map each saved target interval back to an exact extracted interval, then slice
the text between consecutive targets. Record both coordinate systems and the
exact intervening text. Classify a same-window gap as empty, whitespace only,
or containing non-whitespace. Also count alphanumeric characters and nonspace
runs for description. The strict continuity criterion is zero internal gaps
containing non-whitespace. A punctuation-only gap would therefore count against
strict continuity and would be described separately from skipped words.

Require agreement between a regular-expression coordinate map and an independent
character scan before reporting. Check that matches and gaps partition both
windows, and retain all counts and text locally. Freeze the audit code, verifier,
protocol and saved E99 inputs before reading the saved gap contents. Replay uses
saved spans and does not rerun matching, reparsing, source retrieval or models.

End after the gap audit and verification. Findings concern the extracted Burton
text and package English under E99's whitespace view. Semantic benchmark capacity
remains 0/4 and untouched units remain zero.
