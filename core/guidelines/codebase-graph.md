# Codebase Graph (graphify)

Read when you need to understand a large or unfamiliar codebase, find what a change affects, or brief an agent without making it explore. A graph lets you ask "what calls X / what does X touch" in a few hundred tokens instead of reading or grepping dozens of files. graphify is installed by `/setup`. On Windows, run its CLI as `python -m graphify <command>`; the bare `graphify` command may not be on PATH.

## When it pays

- **Use it:** repos with roughly 150+ source files, multi-session work on the same repo, reviews and refactors where the blast radius matters, onboarding into code you didn't write.
- **Skip it:** small repos, single-file fixes, or when you already know the exact files. Reading 2–3 known files is cheaper than any query.

## Build once, keep it fresh

- **First build:** run the graphify skill on the repo root (`/graphify .` in Claude Code). On a **code-only** repo it extracts structure from the source code directly: no LLM, no token cost. Docs, papers, and images go through LLM extraction, which costs tokens. Include them only when the question is about them, and never use `--mode deep` by default.
- **Large graphs:** add `--no-viz` (skips the HTML) for repos over a few thousand nodes.
- **Keep it fresh:**
  - `python -m graphify update .` re-extracts changed code files without an LLM. Run it after pulling or switching branches, and before a review.
  - `python -m graphify hook install` adds a post-commit hook that does the same automatically. It writes to `.git/hooks`, so ask the user first.
  - After refactors that delete code, use `update . --force`.
- **Staleness check:** if `graphify-out/graph.json` is older than the latest commit or your own edits, update before trusting it.
- **Git:** `graphify-out/` is generated output, so add it to `.gitignore` unless the project deliberately shares the graph.
- **Don't:**
  - run `graphify claude install` (it writes its own section into the project's `CLAUDE.md`; this guideline replaces it);
  - run the MCP server (`--mcp`) or `watch` (background process);
  - use the Neo4j/Obsidian exports, unless the user asks.

## Query it in this order

1. **Orientation:** read the top of `graphify-out/GRAPH_REPORT.md` (overview, main communities, hub nodes), not the whole file.
2. **Focused question:** `python -m graphify query "<question>" --budget 1500`. BFS by default (what is X connected to); `--dfs` traces a chain (how does X reach Y). Matching is literal substring on node labels, so use the code's own identifiers (`TenantGuard`, `resolveScope`), not prose synonyms.
3. **One thing:** `python -m graphify explain "X"` (a node and its neighbours) or `python -m graphify path "A" "B"` (the shortest connection).
4. **Blast radius:** `python -m graphify affected "X" --depth 2` lists what depends on X: callers, dependents, tests. Use it before changing a public symbol and before reviewing a diff.
5. **Then read only those files.** The graph tells you where to look; the code is the truth.

## Trust, but verify

- The graph is a map, not proof. Edges are tagged EXTRACTED (from the code), INFERRED, or AMBIGUOUS. Confirm anything you're going to act on or report by reading the code.
- A query that returns nothing usually means a vocabulary mismatch or a stale graph, not "no usages". Retry with the exact identifier, then fall back to grep.

## In briefs (the Lead)

- **Reviewer and tester briefs:** for each public symbol the diff changes, run `affected` and paste the resulting file list into SCOPE/CONTEXT. The specialist then reads those files instead of exploring.
- **Executor briefs:** paste the relevant `explain`/`path` output when the task crosses modules, so the executor doesn't rediscover the structure.
- **Fan-outs:** for multi-agent work, the *analyze* task type starts from `GRAPH_REPORT.md` when `graphify-out/` exists (see `protocols/task-types.md`).
