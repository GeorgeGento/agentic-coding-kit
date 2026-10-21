# JavaScript & TypeScript

Read before writing or editing JS/TS code. Language-agnostic rules stay in [`coding-standards.md`](../coding-standards.md); framework rules live in [`angular-frontend.md`](../angular-frontend.md) and [`backend-nodejs.md`](../backend-nodejs.md).

## TypeScript standards

- **`strict: true`.** No `any` — use `unknown` + narrowing, or a proper union/generic. If `any` is truly unavoidable, isolate and comment why.
- **Explicit return types** on every exported function, method, and `computed()`.
- **No `as any` / `as unknown as X`** to silence the compiler — fix the underlying type.
- **No TS `enum`.** Use a `const` object with `as const` and export the derived type:

  ```ts
  export const OrderStatus = { Draft: 'draft', Sent: 'sent' } as const;
  export type OrderStatus = (typeof OrderStatus)[keyof typeof OrderStatus];
  ```

## Idioms

- **Prefer `for...of` over `.forEach`** in code you write or touch: it allows `break`/`continue`/`await` and avoids a callback per item. Don't bulk-rewrite untouched code.

## Documentation (JSDoc)

- **JSDoc every exported JS/TS function** with an `@example` block — **unless** the name is self-explanatory from its signature (e.g. `isEmpty(arr)`, `toKebabCase(str)`). When in doubt, add it.
- JSDoc explains **why / how to use**, not what the code literally does.
