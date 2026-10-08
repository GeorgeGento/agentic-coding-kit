# Node.js, NestJS & MongoDB

Read for backend / API work. Targets **Node.js 24.x LTS**, **NestJS latest stable**, **MongoDB 8.0 LTS** (8.3 latest). General code rules: [`coding-standards.md`](coding-standards.md). Security: [`security-privacy-logging.md`](security-privacy-logging.md).

## Architecture (layered)

- **Thin controllers:** transport, guards, pipes, and response mapping only. **Services** hold use-case logic. **Repositories / data services** handle persistence. Keep business logic out of controllers.

## Dependency injection & extensibility

- **Use DI for dynamic injection and extensibility — never manually instantiate dependencies.** NestJS is DI-first; lean into it.
- **Program to an interface + DI token**, then bind the implementation with a custom provider: `useClass` (swap per environment), `useFactory` (async / config-driven construction), `useValue` (constants/mocks), `useExisting` (alias). Swapping an implementation must not require editing its consumers.
- Build configurable, reusable modules as **dynamic modules** (`forRoot` / `forRootAsync`); export shared providers so other modules can reuse them.

## Configuration

- Use a validated config module (e.g. `@nestjs/config` + a schema). Never read raw `process.env` throughout the code; centralize and validate required values at startup.

## Validation (every boundary)

- Validate `body`, `params`, and `query` at every endpoint, and reject unknown fields. Pick **one** schema library per project and be consistent.
- **Choosing the library:** if the project already uses a schema library (e.g. Joi), use that, and don't introduce a second one. If none is in use, **ask the user** before adding one, recommending Zod for the reasons below.
- **Recommended for TypeScript: Zod** — `z.infer` gives one source of truth for the type *and* the runtime schema, and schemas can be shared frontend↔backend (use `nestjs-zod` for controller integration; `.strict()` / `z.strictObject` to reject unknown fields). **Joi** is an acceptable alternative (mature, rich validators) but has no static type inference, so types drift from schemas. Don't hand-roll `if (!x) throw` when a schema can express the constraint.
- Return a consistent validation error shape with sanitized issues (no sensitive field values).

## API design

- Consistent success **and** error response shapes; stable error codes; user-safe messages; enough server logs to debug without leaking internals.
- Request body size limits; validate content type, file type/size, pagination, and sort/filter fields. Protect write/admin endpoints with authentication, authorization guards, rate limiting, and audit logging (see [security](security-privacy-logging.md)).
- Never enable Swagger / API docs in production unless explicitly requested — it exposes routes, DTOs, and auth flows.

## MongoDB / Mongoose

- Use Mongoose schemas or well-defined repository services. Validate `ObjectId`s; index queried fields; use bounded pagination; avoid unbounded queries/exports.
- **Never trust input — prevent NoSQL injection:** reject client-controlled operators (`$where`, `$regex`, `$expr`), raw query-JSON passthrough, and unknown fields unless explicitly allowlisted. Use explicit query builders.
- Use transactions for multi-document writes that must stay consistent; handle duplicate-key errors and races explicitly.
- **Never delete or drop data, collections, or databases without an explicit user command.** All destructive DB operations require a separate, explicit instruction.

## Testing

- Cover services, controllers/endpoints, and repositories — see [testing.md](testing.md) for the testability + coverage standard. Tooling: Jest/Vitest + the NestJS testing module, `supertest` for HTTP, an in-memory or disposable test DB (e.g. `mongodb-memory-server`) for repository/integration tests. Run lint / build / test before declaring done.
