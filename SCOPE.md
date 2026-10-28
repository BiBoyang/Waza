# Scope

Waza is the small set of engineering skills I use every day. Ideas are welcome, and each one is judged against the bar below. Read it before opening an issue or a pull request.

## The bar

An idea or feedback issue stays open only if it clears both parts:

1. **Observed failure.** Something went wrong in a real session: what you ran, what the skill did, and what you expected. A hypothetical improvement ("it would be better if...") does not clear this part.
2. **Fits Waza.** It does not match anything in [`.out-of-scope/`](.out-of-scope/), and it is not a configuration option, a branch for one harness, or a tweak for one person's workflow. Those belong in your own `CLAUDE.md` or `AGENTS.md`, or in a fork.

Size does not matter: a one-word fix and a rewrite face the same bar. Reactions and +1 comments do not count toward it.

## The set stays small

Eight skills: five own the stages of the [AI coding rules](docs/ai-coding-rules.md), and `/read`, `/learn` and `/write` support any stage. New behavior folds into an existing skill or composes from several, and new skills are not being added.

## Already decided

Each file in [`.out-of-scope/`](.out-of-scope/) records one decided question and why. Read them before filing:

- [`skill-name-prefix.md`](.out-of-scope/skill-name-prefix.md): no `waza-` prefix on every skill
- [`harness-name-collisions.md`](.out-of-scope/harness-name-collisions.md): a built-in command keeps its name, Waza renames
- [`remember-skill.md`](.out-of-scope/remember-skill.md): no memory skill
- [`third-party-providers.md`](.out-of-scope/third-party-providers.md): no new search or fetch provider in `/read` without a gap the current tiers cannot cover
