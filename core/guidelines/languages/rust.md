# Rust

Read before writing or editing Rust code. Language-agnostic rules stay in [`coding-standards.md`](../coding-standards.md); packaging rules (features, workspaces) live in [`library-design.md`](../library-design.md).

- **One shared `CARGO_TARGET_DIR` per machine, outside every repo** (e.g. `<local app data>/cargo-target/shared`, set as a user env var so every tool picks it up). Every dependency compiles once. Parallel worktree agents use a second one (`.../cargo-target/worktrees`), because the OS locks the running dev app's executable and a worktree build into the same folder fails to link. **Never create a target folder per task, agent, or spike** (they each compile the whole dependency tree, 1.5–5 GB, and pile up), and never brief an agent to. Builds wait on Cargo's folder lock; that's expected. `cargo clean` the shared folder occasionally (old dependency versions are never removed, e.g. past ~40 GB).
- Apps and binaries commit `Cargo.lock`. A crate shipped as source inside another package (e.g. an npm package) doesn't: the consumer resolves its own lock.
- Keep the dev profile slim (reduced `debug` info) when build size or time hurts.

## Test fixtures with temp dirs

Fixtures that own a temp dir **and** something holding files in it (a SQLite store, a log, an engine) leak silently on Windows, which refuses to delete open files (and `let _ = remove_dir_all(..)` hides the failure). Check:
- **Fields drop in declaration order:** the guard that removes the folder is the **last** field, after every store.
- **`impl Drop for Fixture` runs before any field drops:** removing the folder there runs while the stores are still open. Use a small `RemoveOnDrop(PathBuf)` guard as the last field instead.
- **Background tasks keep stores open:** a job spawned with an `Arc` clone (a trim loop, a wake timer) never ends under a fake clock. The fixture's `Drop` closes what it created first (track `Weak` handles).
- **`Arc` cycles keep stores open:** a hook or closure that captures an `Arc` of the object holding it. Break it at the end of the test (`*hook = None`).
- Locals are fine: they drop in **reverse** order, so `let env = ...; let store = env.store();` closes the store first.

Then run the suite and count temp leftovers (testing guideline: tests leave no trace).
