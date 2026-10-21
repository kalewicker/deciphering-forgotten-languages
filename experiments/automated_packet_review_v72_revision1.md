# E72 isolation revision 1, before any model review

The initial deterministic probe could read the packet and MEMORY.md, but could
not read the project report/other temporary canary or write the packet. No model
review was launched and no review findings exist. A parent home-directory deny
did not override Codex's more specific runtime read roots. Preserve the original
protocol, registration, code and failed probe unchanged.

Add explicit deny rules for the Codex memory and session directories, including
resolved paths, and probe the memory summary and an actual saved session file as
well as MEMORY.md. Require all protected reads to raise PermissionError. Do not
accept an absent file as evidence of a denied read. Packet hashes, prompt, review
scope, one-model-attempt budget, criteria and exposure limits remain unchanged.
If these checks fail, do not launch a review or weaken the isolation claim.
