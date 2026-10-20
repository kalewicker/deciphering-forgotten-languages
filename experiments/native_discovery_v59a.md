# E59a receipt-schema correction

The original E59 preflight was frozen and its first execution stopped at the E42
receipt assertion before producing any page audit. The runner demanded exact
artifact-dictionary equality, but E42/E50 receipts contain an additional local
`path` field. This is an implementation error, not a declaration-gate failure.
Preserve the original registration, code, tests and preflight unmodified, plus
the failure record `data/v59/failure.json`.

Only correction: compare `transport_complete is True`, original body SHA-256
and original body byte count, permitting additional receipt fields. Each complete
receipt remains hash-frozen. Regression fixtures cover both existing receipt
schemas and incorrect hash, size and transport. The production declaration audit
and decision rules remain byte-identical; the same eleven captures, query,
uniform gate and proposed future budget apply. No route or outcome was inspected
by the aborted runner. The original reference-page exposure remains disclosed.

New registration/config/code are frozen before resuming into a fresh `data/v59a`
directory; the experiment report occupies `runs/000059_native_discovery`. The
old preflight and failure are included in the corrected input hashes and final
seal. Zero requests, no new captures, substitutions, scoring or admissions.
