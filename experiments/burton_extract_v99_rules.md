# E99 development findings and exact extraction rules

Inspection of the fixed structures shows four empty anchors immediately preceding
another anchor in one pagenum span: 2/3,130/131,286/287,288/289. Only the second
has an adjacent printed label. They are not demonstrated to be nested page labels
or separate printed boundaries. Preserve the first as an unlabelled anchor with
no invented printed label. An unlabelled anchor outside required boundaries does
not define a tested window. All six required anchors have their own labels.

For every numeric or Roman Page_* anchor, record its text offset. If its immediate
next sibling is a string beginning with optional whitespace and [Pg suffix],
require that suffix to equal the anchor suffix exactly, and remove only the label
characters from that text node; preserve preceding whitespace and following prose.
If the next sibling has no such label, record label_status=unlabelled and remove
nothing. Reject mismatching labels or reuse of a label node. Do not call an
unlabelled anchor a verified printed boundary. Required 252..257 must be labelled,
unique and ascending. Numeric anchor IDs must retain the observed sequence 1..351.

Never discard an entire pagenum container. Keep surrounding and nested text under
the original exclusion and block/newline specification. Validate full extraction
and offsets with a separately written stack traversal before scoring. Raw source
bytes and E98 remain untouched. This is a disclosed development choice made before
any wording results, not an after-score repair or changed comparison criterion.
