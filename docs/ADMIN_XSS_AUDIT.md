# Admin XSS Audit

**Audit date:** 2026-07-21  
**Scope:** `apps/admin/src`, admin authentication transport, and browser-facing session data  
**Result:** No direct HTML/JavaScript injection sink was found. The previously exposed browser tokens have been removed from Web Storage. A deploy-time Content Security Policy remains tracked separately as `PROD-017`.

## Checks performed

The audit searched every admin source file for:

- `dangerouslySetInnerHTML`, `innerHTML`, `outerHTML`, `document.write`, `eval`, `new Function`, `srcDoc`, and `javascript:` URLs;
- authentication data in `localStorage` or `sessionStorage`;
- dynamic `href`, `src`, router navigation, `window.open`, object URLs, and HTML/Markdown rendering libraries;
- user/API strings rendered into DOM attributes or executable contexts.

It also reviewed the login, session bootstrap, Axios interceptors, route guard, worker-document download flow, legal pages, navigation configuration, and `next.config.ts`.

## Findings

### Resolved — P1: authentication credentials in `localStorage`

The access token, refresh token, and cached admin user were readable by any JavaScript executing in the admin origin. The storage module and its call sites were removed.

Current behavior:

- refresh token: server-set `HttpOnly`, `SameSite=Lax` cookie, `Secure` outside local development;
- access token: Zustand memory only, with a five-minute default TTL;
- CSRF token: signed and bound to the server-side refresh-token family, held in memory and sent in `X-CSRF-Token`;
- page reload: cookie-backed bootstrap obtains a fresh in-memory access token;
- concurrent `401` responses: one shared refresh promise prevents accidental token replay;
- logout: refresh and access tokens are revoked and browser cookies are cleared.

The remaining `localStorage` use stores only the non-sensitive notification badge count (`admin_alerts_seen`).

### No finding: executable HTML sinks

No direct HTML injection API, inline HTML parser, Markdown-to-HTML renderer, dynamic script source, or `javascript:` URL exists in the audited source. API-provided text is rendered through React text nodes, which are escaped by React.

### No finding: dynamic navigation

Dynamic routes are constructed from application-owned route constants or numeric backend identifiers. The login page does not redirect to a caller-provided `next` URL. Worker-document tabs use `noopener,noreferrer`; local downloads use browser-created blob URLs, and remote document URLs come from the authenticated storage API.

### Open — P1 defense in depth: admin Content Security Policy

`apps/admin/next.config.ts` does not yet define a production CSP or the complete browser security-header set. This is not an identified injection path, but a CSP materially reduces impact if a future XSS defect is introduced. It remains `PROD-017` so its Sentry, API, image, and deployment origins can be tested without weakening the policy with broad wildcards or unsafe script directives.

## Residual risk and release action

- Deploy admin and API over HTTPS on the same registrable site (for example `admin.annaiillam.in` and `api.annaiillam.in`) so `SameSite=Lax` session cookies work without cross-site relaxation.
- Keep `BACKEND_CORS_ORIGINS` an exact allowlist; credentialed CORS must never use `*`.
- Complete `PROD-017`, dependency scanning, and an independent production security assessment before public launch.
- Re-run this source audit whenever HTML rendering, rich text, Markdown, external URLs, or third-party scripts are introduced.

## Verification

- Admin authentication/local-storage search: no authentication token or user persistence remains.
- Dangerous-sink search: no executable HTML/JavaScript sink found.
- ESLint: 0 errors (8 existing warnings).
- Admin unit/security tests: 21 passed.
- Next.js production build: passed, including TypeScript and 34 routes.
- Backend auth and route-guard suite: 52 passed.
- Backend focused Ruff: passed.
- Clean PostgreSQL migration chain: passed through `b14d9e2c6f80`.

This is a source-level engineering audit, not a penetration-test attestation.
