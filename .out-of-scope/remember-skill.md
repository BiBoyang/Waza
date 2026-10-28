# No memory skill

Requested in [#61](https://github.com/tw93/Waza/issues/61): add a `/remember` skill that saves what was learned to memory or a file.

Decision: not planned. Remembering is the agent platform's job. Claude Code already persists durable context through `CLAUDE.md` and auto memory, and Waza skills read that context in their Durable Context Preflight instead of owning storage. Keeping notes in `CLAUDE.md` or the agent's memory feature gives the same result today.
