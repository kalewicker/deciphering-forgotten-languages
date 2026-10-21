# Starting a fresh Codex review without project memory

The installed CLI was `codex-cli 0.163.0-alpha.10.2`. Its help and the official
documentation confirm per-run configuration overrides and ephemeral execution.
The documented memory settings are `memories.use_memories=false` (skip injecting
existing memory) and `memories.generate_memories=false` (exclude new threads
from memory-generation inputs). These overrides do not delete or rewrite the
user's memories or global preferences.

A minimal new CLI session, in a directory containing only review materials:

```sh
codex exec --skip-git-repo-check --ephemeral \
  -c memories.use_memories=false \
  -c memories.generate_memories=false \
  -C "/absolute/path/to/packet-only-folder" \
  "Review only the supplied packet and disclose your exposure and uncertainty."
```

Use a new invocation rather than `resume` or `fork`. A new desktop chat alone
does not establish that persistent memory was excluded. `--ephemeral` controls
local session-file persistence; it is not by itself a memory-off switch. The
minimal command above also does not prevent file access to memories or reports.

E72 adds stronger controls: no user config, no project instruction injection,
disabled memories/hooks/plugins/apps/subagents/browser tools, no tool network,
and an explicit filesystem profile protecting the home directory, Codex memories
and saved sessions, and unrelated temporary files. The packet is read-only.
The coordinator froze all inputs and ran deterministic read/write probes before
launching a model. The initial parent-directory deny was insufficient because
of more specific Codex runtime read roots; its failed probe was preserved and
the review was not launched until explicit directory denies passed.

Those probes test the named files and current sandbox behavior. They do not
prove absence of pretrained familiarity, every possible side channel, or model
family correlation. This is a fresh automated, source-disclosed developmental
review, with no automatic independent scientific or semantic admission. The
first return and tool trace are retained locally for exposure assessment.

References checked on 2026-10-20:
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
and [official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
Authentication and service-side retention are separate from these memory and
local-persistence controls.
