# AI Coding Rules

[中文](ai-coding-rules.zh.md)

Twenty rules, grouped in the order a task moves, ready to paste into your agent's instructions. In Waza, `/think` owns Need, `/health` owns Rules, `/ui` covers interfaces, `/hunt` owns Debug, and `/check` owns Review, Ship and Retro.

## Need

1. Move from spelling out implementation details to wishing out loud. Today's models are strong enough: say what you want, set a high bar and a deep task, and stop worrying that the AI can't do it.
2. Tell your agent the background and the goal, and leave the technical details to it: why this exists, who it's for, and what you'd call the best result. Let it pick the implementation. Learn to let go.
3. Use the best model available. A weaker one costs you twice: the back-and-forth of rework, and the time it wastes.
4. Before a new feature, setting or switch goes in, have the agent ask you first. Features, switches and copy nobody uses never get added, and over time the answers become your product's own conventions.
5. Your idea can be big, but each piece of work should be the smallest usable version. Don't write a lot of code at once; commit as you go, so anything that breaks can be reverted.

## Rules

6. Teach your agent how you talk. "Look at" or "analyze" means read the code and report, without editing; "fix" or "change" means do it. Once a change is verified it can commit on its own; publishing and deleting still come back to you.
7. Beyond the key project requirements, `AGENTS.md` and `CLAUDE.md` hold only what the code can't tell: the non-obvious rules, and the options you already rejected.
8. Don't rely on the prompt alone for rules the agent must follow; it can slip. Enforce them with hooks or check scripts, and count the work done only once they actually ran and passed.

## Code

9. Before writing code, have the agent say what it will change and what features or behavior that affects. It fills in your picture, so you can steer the decisions that follow.
10. Have the agent add a script that lets it verify results in this project, run it at the right moments and after each feature, and show you the output. Over time those scripts become the project's own agent test suite.
11. When several agents work at once, give each its own git worktree, and have each commit only the code it changed, never anyone else's.

## Debug

12. Find the cause before touching the bug. If two fixes didn't work, add logging and look at real data and runtime behavior instead of guessing.
13. After three failed attempts, clear the context and start over: restate the problem, the goal, and what was already tried.

## Review

14. Keep the agent that writes the code apart from the agent that reviews it, so one can't pull the other off course.
15. Cap review at three rounds so it doesn't run forever. From the second round, look only at what changed, not at what was already reviewed.
16. The riskier the change, the deeper the check. Deletion, billing and publishing are one-way doors: look at them yourself, click through, and see the real result.

## Ship

17. Every commit says what changed, how it was verified, and how to roll it back. Later on, the git history itself is some of the best context your agent has.
18. Anything user-facing goes to you first, or to a group of early adopters, never everyone at once. A beta update channel in your app guards against a bad full rollout and is the responsible thing to do for users.

## Retro

19. Every production bug and user report gets a test case that runs before each release, so the same hole isn't hit twice. When you switch models, run the whole set again to see whether the new one holds up.
20. Teach the agent to fix the class, not the instance: fix the same problem everywhere it appears. The same goes for feature work and visual polish, so one spot changes and the others aren't forgotten.
