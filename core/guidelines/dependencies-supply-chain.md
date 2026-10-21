# Dependencies & Supply-Chain Security

Read before installing or upgrading any package, or trusting third-party code — including skills, MCP servers, plugins, and source builds.

## Versions

- Use the **latest stable/LTS that is at least 14 days old** when installing or scaffolding — never outdated or vulnerable versions. Targets as of **June 2026** (re-check periodically):
  - **Node.js 24.x LTS** (current Active LTS)
  - **Angular 22** (latest stable; v21 and v20 are in LTS support windows)
  - **MongoDB 8.0 LTS** (8.3 is the latest rapid release)
  - **Tailwind CSS 4** (latest stable)
- New projects: latest stable for **all** dependencies from the start.
- Prefer pinned versions + committed lockfiles for applications. Avoid floating ranges, unpinned git branches, remote install scripts, and opaque binary downloads.
- **Release cooldown (14 days).** Never install, upgrade, override, or pin any version — direct or transitive — published less than 14 days ago. Fresh releases are the window in which compromised publishes go unnoticed. Check `npm view <pkg> time --json`; install with `npm install --before=<today-14d>` (pnpm: `minimumReleaseAge`; uv: `--exclude-newer`). If only a newer release fixes an advisory, don't install it: report "wait until <date>" and list the advisory as open. Put the cutoff date in every brief that touches dependencies.

## Pre-install checks (every install/upgrade)

Run these for the exact version you will install; any failure blocks the install:

1. **Age** — version published ≥ 14 days ago (above).
2. **Integrity & provenance** — `npm view <pkg>@<ver> dist.integrity dist.signatures dist.attestations`: integrity hash present; prefer versions with provenance attestations. After install, `npm audit signatures` must pass.
3. **Diff against the previous version** — new or changed maintainers, newly added lifecycle scripts (`npm view <pkg>@<ver> scripts`), a changed `repository` URL, or an unexplained jump in size/deps are red flags: stop and report.
4. **Lockfile** — commit it and install with `npm ci`; every `resolved` URL points at the expected registry and carries an `integrity` hash.
5. **Advisories** — `npm audit` clean (see below).

## Vulnerabilities are a blocker

- After any install/update, run `npm audit` (or the equivalent) and fix **all** findings before continuing. **0 vulnerabilities is the only acceptable state.**
- Use `overrides` (npm) / `resolutions` (yarn) to force-fix vulnerable transitive deps. Use `npm audit fix --force` only after explaining the impact and getting approval.
- Never ship known vulnerabilities unless the user explicitly accepts a documented upstream-only risk with a mitigation. Re-audit after dependency changes, generator/plugin use, or long time gaps.
- Don't keep scaffold helpers (`create-*`) as runtime dependencies. Never install deprecated packages — find the maintained replacement.

## Package selection — reputation first

Before installing any package, verify **all** of:

1. **Popular** — >1k weekly downloads (prefer >100k for core deps).
2. **Maintained** — a commit within the last ~6–12 months.
3. **Reputation** — stars (>500 utilities, >5k frameworks), healthy open/closed issue ratio, responsive maintainers.
4. **Clean security history** — `npm audit` + `github.com/advisories`. An unfixed high/critical advisory is an automatic reject.
5. **Official/canonical** — prefer the official org (`@nestjs/*`, `@angular/*`) over third-party wrappers.
6. **Minimal transitive bloat** — if a 10-line utility pulls 200 subdeps, find a leaner option or inline it.

Red flags that force a reject: typosquat-looking name, single author with no org, <50 stars, last publish >2 years ago, "no fix available" advisory, license ambiguity.

Extra rules when **adding or recommending a new direct dependency**:

- **Ask before adding.** Propose it with the one-line summary below and say why stdlib, existing deps, or a few lines of own code won't do. Never add one silently.
- **Established packages only** — first published ≥ 6 months ago, passes every check above (downloads, stars/reviews, issue health, maintenance, advisories), and ≥ 1.0 for anything on a core path.
- **No install-time scripts** unless the package genuinely needs them (native builds) and you've read them.

When you propose a package, state one line: weekly downloads, stars, last release date, chosen version + its publish date, provenance yes/no, install scripts yes/no, advisories. (Example: prefer `exceljs` over `xlsx`, which has unfixed ReDoS + prototype-pollution advisories marked "no fix available".)

## Supply-chain review (source builds & third-party agent code)

- Treat building from source — and any AI skill, hook, plugin, MCP server, subagent, or slash command — as **executable supply-chain code**. Audit before enabling.
- Review dependency lifecycle scripts before install/build (`preinstall`, `install`, `postinstall`, `prepare`, `prepack`, `build.rs`, Makefiles, CI workflows, Dockerfiles). High risk: scripts that curl|bash, download binaries, modify shell profiles, read SSH/keychain, hit cloud-metadata endpoints, or exfiltrate env vars.
- Search for exfiltration patterns: outbound HTTP/DNS beacons, telemetry/paste/webhook URLs, base64 blobs, crypto-mining, credential/SSH/GPG/browser-profile reads, cloud-metadata access.
- Check provenance: stars/forks, recent commits/issues, maintainer identity, ownership transfers, archived status, official vs impersonating fork. Cross-check package metadata against repo links (`gh repo view`; `npm view <pkg> version time maintainers repository dist.integrity`). Include typosquatting + dependency-confusion checks.
- Inspect lockfile/manifest diffs: new deps, maintainer changes, major version jumps, registry/integrity changes.
- **MCP servers are elevated risk** (they expose tools and credentials). Prefer trusted remote HTTP MCP servers or audited local stdio servers; avoid `npx -y <package>` MCP servers unless the package passed review. Least-privilege scopes; never share broad production tokens.
- Prefer sandboxed/disposable environments for untrusted source; clear sensitive env vars first. If a risk can't be eliminated, stop and ask with the evidence, mitigations, and safer alternatives.
