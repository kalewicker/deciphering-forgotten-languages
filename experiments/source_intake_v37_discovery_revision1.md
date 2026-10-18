# v37 discovery interface revision 1

The first four-query web call returned one flat organic-result list without
per-query attribution. Its complete response is preserved in
`data/v37/discovery/search_batch_raw.json`. It cannot support the registered
two-slot-per-query nomination rule and supplies no eligible nominations.

Before any raw acquisition or scientific comparison, repeat the same four
queries individually and save each response under its exact query/index. This
is a recorded provenance-interface repair: maximum search executions becomes
eight (the initial four batched plus these four individual), with four distinct
query strings unchanged. No additional search terms, candidate substitutions,
raw routes, fallbacks, reviewer evidence, capacity criterion or scientific
admission rule are added. Do not pool the unattributed batch into nominations.
The original discovery failure remains in the request accounting.
