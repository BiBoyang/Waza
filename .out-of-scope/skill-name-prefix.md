# No `waza-` prefix on every skill

Requested in [#59](https://github.com/tw93/Waza/issues/59): rename every skill to `waza-check`, `waza-think` and so on, so names never collide with other installed skills.

Decision: not planned. `/check` and `/think` are typed many times a day, and a prefix adds typing and visual noise on every one of them for a brand benefit that is far smaller than the cost. When another installed skill duplicates a Waza skill, remove the duplicate and keep a short skill list. Plugin installs already namespace skills as `/waza:check`.

A real collision with a built-in command is a different case, covered by [harness-name-collisions.md](harness-name-collisions.md).
