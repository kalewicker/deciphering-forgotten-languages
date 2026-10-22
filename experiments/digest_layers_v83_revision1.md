# E83 pre-execution receipt-schema compatibility revision

The original E83 preparation froze a runner and verifier that assumed every
receipt stored artifact hashes as metadata objects. Before any diagnostic run,
schema inspection found E82 instead stores the hash directly as a string.
No E83 systematic diagnosis had executed; no output or outcome was available.

Preserve the original protocol, registration, code and fixtures unchanged.
New revision1 runner/verifier accept the two existing formats without changing
any receipt bytes. E63 uses its metadata object's sha256; E82 uses its string.
The original source receipt files remain hash-bound and unmodified. No source
hash, criterion, input capture, marker, transformation budget or scientific
claim changes. The output goes to a new revision1 directory.

The revision registration includes the complete original input ledger, original
registration and new revision files/tests. New fixture checks bind both formats.
The independently formulated verifier also accepts the exact two formats.
Only the revision1 execution is to run; do not run the incompatible originals.
