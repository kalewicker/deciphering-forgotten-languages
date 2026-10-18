# Publication scope and ongoing commits

Research resumed with experiment 41 after the user's continuation instruction.
Publication does not change any frozen result. No natural FL decipherment has been
validated; structural recovery, copied English and source metadata are separate
from meanings and immediate source identity.

The public `main` branch contains project source, test code, experiment
registrations, small benchmark specifications, scripts and reports. Historical
reports and registrations are preserved as written. Their local artifact links,
absolute acquisition paths and hash ledgers document the original workspace;
they do not imply that those artifacts are included in a public clone.

The local `local-evidence-2026-10-18` branch additionally preserves the complete
`data/`, `runs/` and `benchmarks/` research snapshot. Its initial publication
checkpoint is `b84e7b0`; subsequent turns append commits while preserving that
history. This branch is not pushed. It includes downloaded source documents, extracted text, review
packets, synthetic panels and generated predictions. Environments, bytecode,
operating-system files and editor/assistant settings are not research artifacts
and are excluded from both branches. A local archive commit is a checkpoint,
not an off-device backup.

The user requested a commit and push at the end of every work turn on
2026-10-18. Public changes are committed to `main` and pushed to `origin/main`;
generated research artifacts are committed on the local evidence branch. A
work turn is not reported as successfully published until the remote commit
and public tree agree with the local `main` branch.

Public exclusions include third-party source documents and review packets,
the multi-gigabyte run archive, acquisition inputs and the five large generated
v7-v11 panels. They remain intact locally. No license for third-party material
is granted or implied. A project-wide software license has not been selected.

## Verify a public clone

Python 3.12+ and `uv` are required:

```sh
uv sync --frozen
uv run python scripts/test_public_snapshot.py
```

The public runner explicitly lists archive-dependent tests it excludes. It does
not replace the historical full-suite result of 337 passing tests in the complete
workspace. An isolated export of the public scope passed all 298 included tests;
39 archive-dependent tests are excluded. The unmodified original tests remain
public; four older modules load
the historical lexicon during import, and four additional cases require frozen
source/lexicon artifacts. The full suite needs the local research snapshot:

```sh
uv run python -m unittest discover -s tests -q
```

Original experiment runners and evidence-verification scripts also require the
excluded archive. PDF acquisition/inspection scripts additionally used pypdf,
pypdfium2 and Pillow from the documented bundled runtime; these optional tools
are not installed by the base package. No missing historical material should
be redownloaded and silently substituted under its old hash or test identity.

When resuming research, use a new registered experiment and preserve the prior
artifacts. Avoid switching the current worktree to the archive branch: its
tracked evidence overlaps the ignored evidence already present. Inspect it with
`git show local-evidence-2026-10-18:<path>` or use a separate clone/worktree.
