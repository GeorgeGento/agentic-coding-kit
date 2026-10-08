# Performance

Read before writing or reviewing any code. **Performance is a default, not a later pass**: pick the efficient shape up front when it costs no clarity. Don't micro-optimize without evidence. Do avoid the structural mistakes that are expensive to undo once data grows.

## Know your data size

- Before choosing an approach, state the expected size: rows, items, requests/sec, payload. Tiny bounded inputs (a 5-item config list) get the most readable code; anything user- or data-driven is assumed to grow.
- Note the complexity of hot paths in your report when it isn't obvious (`O(n)` per request, `O(n·m)` on import).

## Algorithms & loops

- **One pass over the data, not several.** Don't `filter` → `map` → `filter` → `reduce` over the same large array when a single loop or `reduce` does it. Chained array methods are fine when the input is small or readability clearly wins.
- **No nested scans for lookups.** `a.find()` inside a loop over `b` is `O(n·m)`. Build a `Map`/`Set` (or dict) once, then look up in `O(1)`.
- Hoist invariant work out of loops (regex compilation, date parsing, config reads, `JSON.parse`).
- Don't copy in a loop: `acc = [...acc, x]` or `{...acc, k: v}` inside `reduce` is quadratic. Build locally and freeze once if immutability matters.
- Sort once, not inside loops; prefer streaming/iterators for large inputs over materializing everything.

## Databases

- **Every query has an index that serves it.** Filter + sort fields of each production query must be covered. For compound indexes, order fields **Equality → Sort → Range** (ESR). Add the index in the same change as the query (schema/migration), not later.
- **Verify with the planner** (`explain()` / `EXPLAIN ANALYZE`) for new or changed queries on large collections: no collection scan, no in-memory sort, examined ≈ returned.
- **No N+1.** Never query inside a loop over results: batch with `$in` / `JOIN` / `populate` with care / a DataLoader.
- **Project only needed fields**; never ship whole documents to compute one value. Push aggregation to the DB when it shrinks the payload.
- **Bounded reads always**: pagination with a hard max; prefer cursor/keyset pagination over large `skip`/`OFFSET`.
- Batch writes (`bulkWrite`, multi-row `INSERT`); keep transactions short.
- Avoid unindexable patterns: leading-wildcard / unanchored regex, functions on indexed columns, `$where`, case-insensitive matches without a matching collation index.
- Every index has a write cost. Don't index fields no query uses; remove indexes made redundant by a compound one (prefix rule).

## I/O, network & concurrency

- Run independent awaits concurrently (`Promise.all`), with **bounded concurrency** for large fan-outs (`p-limit` style). Never sequential `await` in a loop over independent items.
- Timeouts on every outbound call; retries with backoff only for idempotent ops.
- Cache expensive, repeatable reads only with a clear invalidation rule and a size/TTL bound. An unbounded cache is a memory leak.
- Stream large payloads/files instead of buffering them whole.

## Frontend

- `OnPush` + signals; `track` on every `@for`; no function calls in templates that recompute every check (use `computed`).
- Lazy-load routes and heavy components; virtual-scroll long lists; debounce/throttle input-driven work.
- Size images (`width`/`height`, `NgOptimizedImage`), avoid layout thrash (batch DOM reads before writes), watch bundle budgets.
- Clean up subscriptions, listeners, timers (`takeUntilDestroyed`, `DestroyRef`).

## Reviewing for performance

Auditors check every change for: loops over the same data that could merge, lookups inside loops, queries without a serving index, N+1, unbounded reads/caches, sequential independent awaits. A missing index on a new production query is a **major** finding, not a nit.
