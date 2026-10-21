# Security, Privacy & Logging

Read for anything touching auth, secrets, user data, or logs. Security is a primary shipping requirement, not an afterthought.

## Security baseline

- Validate and sanitize all user input against injection (XSS, SQL/NoSQL, command, path, template, regex). Validate on **both** client and server; never trust client input. Show a clear, user-friendly message on every validation failure.
- Enforce input constraints: length limits (`maxlength` on the frontend **and** validation on the backend), allowed characters, numeric ranges. Sensible field caps (name 100, description 500, notes 2000, etc.) protect memory and the DB.
- Least privilege everywhere. **No secrets in code, logs, or output.** Centralize and validate config; never scatter raw env reads.
- Parameterized queries / safe ORM-ODM APIs only. Never pass user input to `eval`, dynamic `Function`, shell, filesystem paths, or raw queries without strict allowlisting.
- Security headers by default: CSP where practical, HSTS on HTTPS, `X-Content-Type-Options`, frame protection, referrer policy, tight CORS allowlist (never wildcard CORS with credentials).
- Rate-limit endpoints (sensible defaults; stricter for auth/write).
- Request body size limits; validate content type, file type/size, pagination, and sort/filter fields before processing.
- File uploads: server-generated names, content sniffing, size limits, non-webroot storage, deny executable/scriptable types.

## No remote/CDN dependencies at runtime

- Never load scripts, workers, fonts, or any resource from CDNs or remote URLs at runtime (cdnjs, unpkg, jsdelivr, Google Fonts CDN). Bundle locally via npm and serve from the app — supply-chain safety, privacy, and offline support. Override libraries that fetch remote workers/resources to use the local bundle.

## Authentication, authorization & sessions

- Prefer passkeys/WebAuthn, OIDC, or established identity providers. With passwords: strong minimum length, allow password managers and paste, block breached/common passwords, no forced periodic rotation.
- **Authorization is server-side and object-level.** Never rely on hidden UI, CSS, routes, or client checks. Check ownership/tenant/role on every protected read and write.
- Hash passwords with Argon2id or bcrypt. Never store plaintext passwords, recovery tokens, API keys, or refresh tokens; hash or tokenize lookup-only values.
- Secure cookies for browser sessions: `HttpOnly`, `Secure`, `SameSite=Lax` or stricter, scoped path/domain, idle + absolute timeout, rotation after privilege change.
- Protect auth, password-reset, email-change, MFA, and admin flows against enumeration, brute force, CSRF, replay, and session fixation. Require re-auth or MFA for sensitive actions (payment/role/security changes, exports, destructive ops, key creation).
- **Fail closed.** When a required check can't pass (e.g. 2FA required but not enrolled), issue no session. Return only a short-lived, limited-purpose ticket (e.g. for enrollment), never a full session that the client is trusted to restrict.
- **Purpose tokens** (invite, enrollment, reset, verify) are high-entropy, single-use, short-TTL, stored hashed, and namespaced per purpose, so one kind can't be replayed as another.
- **Protected by default.** Routes require auth unless explicitly marked public (global guard + a public opt-out), so a forgotten decorator can't expose an endpoint. Admin routes are never public.
- **Trust an organisation only via verified identity claims** (e.g. Microsoft `tid`, Google `hd`), never by matching email-domain strings. Revoke sessions immediately when a user loses access.
- Admin panels must never allow deleting the last remaining admin or the currently logged-in user — enforce a backend guard **and** a disabled/hidden frontend control.

## Credentials & passwords (never logged)

- Never log, persist, or store passwords, tokens, or keys to any log, DB, activity log, console, or analytics. Keep them in memory only as long as needed, then clear. Log the **action** ("sudo activated"), never the credential.

## Privacy & GDPR

- Privacy by design. Collect the minimum PII needed; define purpose before storing; avoid special-category data unless required and approved.
- Treat PII as restricted: encrypt sensitive PII at rest, TLS in transit, role-restricted access, and log access/export/delete operations **without** logging the PII itself.
- Field-level encryption for highly sensitive fields (national IDs, health, financial identifiers, tokens, private notes); keep keys in a secrets manager/KMS, separate from the data, with rotation.
- Define retention + deletion for user data, logs, exports, backups, and temp files.
- Support GDPR-style rights where in scope: export, rectification, deletion, consent withdrawal, audit trail.
- Never expose sensitive data in URLs, analytics, `localStorage`, logs, crash reports, screenshots, fixtures, or seed files. Use realistic fake data for demos/tests; never copy production PII into dev/test unless approved, minimized, and masked.

## Logging & debugging

- Structured logging (timestamp, level, service/app, environment, request/correlation ID, concise context). Use the stack's standard logger (e.g. Winston or pino for Node) unless the project already has one.
- Never log secrets, passwords, tokens, `Authorization` headers, cookies, session IDs, keys, payment data, or raw PII — redact before writing.
- Log errors with a stable code, a safe message, a stack trace in secured/non-production logs, and a correlation ID. User-facing errors stay safe and actionable.
- Audit-log security-relevant writes: login/authorization failures, admin actions, data export/delete, key/secret/role changes, destructive operations.
- Logs are rotation/retention-aware; exclude them from git (except a documented `logs/.gitkeep`). Check existing logs early when debugging runtime issues.

## Scripts against real databases

- **Connect through the project's own connection helper/CLI**; never open `.env*` or config files to extract credentials, URIs, or DB names.
- **Confirm the target before every run, dry runs included:** print/read which database, server, and environment the script will hit. The same command can reach a different DB depending on machine and active project config — never assume.
- **Dry run first**; apply only after the user reviews the dry-run output and gives a go. Treat anything named or configured as production as off-limits unless the user names it explicitly.

## Frontend security

- No secrets, session/refresh tokens, or sensitive PII in `localStorage`; prefer secure cookies; encrypt local-only data if browser storage is genuinely required.
- Avoid `[innerHTML]`; if required, sanitize explicitly and document why. Don't bypass the framework's security APIs casually.
- Validate `postMessage` origins exactly (never `*` for sensitive messages); treat payloads as untrusted.
- External links opening new tabs use `rel="noopener noreferrer"`.
- CSS is not access control — don't ship admin-only feature names or controls to users who shouldn't see them.

## Reliable enforcement

- For anything that must be blocked reliably, prefer runtime permissions, hooks, sandboxing, devcontainers, or VMs **in addition** to written rules. Use deny rules/hooks for dangerous commands, protected files, secrets, and unsafe network access where the tool supports them.
