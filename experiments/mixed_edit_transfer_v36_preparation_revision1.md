# v36 preparation repair 1

The first preparation invocation stopped at the frozen token-view ASCII/alnum
assertion, before any fixture file was written and before any prediction or
assessment. Inserted token labels used the profile identifier literally, and
`dense_unknown` contains an underscore. This is a presentation-format failure.

Preserve `data/v36/preflight.json`, the failure receipt and original code snapshots
in `data/v36/preparation_failure/`. Register this repair before changing code.
Remove underscores from the profile portion of inserted token surfaces in both
generator and verifier. Unknown tokens remain distinct, unmapped and unblocked.
Add a regression check that every profile's token strings satisfy the frozen
view format. Do not alter source generation, seed, aliases, edit schedules,
token counts, origins, model, candidate panels, gate or natural-capacity rule.

Seal revised code and the original artifacts in `data/v36/preflight_revision1.json`
before repeating preparation with the same fixed passages. This is not a new
seed or scientific retry. The original preparation failure remains recorded.
