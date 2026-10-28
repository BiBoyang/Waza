# A built-in command keeps its name

Reported in [#69](https://github.com/tw93/Waza/issues/69): the `design` skill shadowed Claude Code's built-in `/design` (Claude Design), and the built-in had no namespaced fallback.

Decision: when a host's built-in command and a Waza skill share a short name, Waza gives the name up and renames its skill. `design` became `/ui` in v3.30.0. Natural-language requests still route to the renamed skill.

This does not reopen [skill-name-prefix.md](skill-name-prefix.md): the fix is one rename where a real collision exists, not a prefix on every skill.
