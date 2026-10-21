# Rust

Read before writing or editing Rust code. Language-agnostic rules stay in [`coding-standards.md`](../coding-standards.md); packaging rules (features, workspaces) live in [`library-design.md`](../library-design.md).

- Put `CARGO_TARGET_DIR` outside the repo (e.g. a per-user cache dir): build caches run to several GB and slow git, search and indexing.
- Apps and binaries commit `Cargo.lock`. A crate shipped as source inside another package (e.g. an npm package) doesn't: the consumer resolves its own lock.
- Keep the dev profile slim (reduced `debug` info) when build size or time hurts.
