# AGENTS.md

## Purpose

This repository is the Annai Illam Staffing Platform.

Use the project Markdown files as the source of truth. Do not copy or re-explain all product rules from memory. Load only the docs needed for the current task, then inspect the existing code before editing.

## Conversation Context Rule

Latest request wins. Use earlier chat only when it directly explains the latest request. If context conflicts with the latest request, project docs, or current code — follow those instead.

## Project Memory

Before reading broader docs, check `.claude/PROJECT_MEMORY.md` for short stable notes that may avoid repeated rediscovery.

Use memory as a cache, not as authority:

- Trust current code and project docs over memory.
- Do not add secrets, tokens, passwords, `.env` values, or private user/client data.
- Add or update memory only after learning a stable fact that is likely useful again.
- Keep memory brief; link to source files/docs instead of copying long explanations.
- Remove or correct stale memory when docs/code prove it wrong.

## Doc Loading Rules

Always read these first for any development task:

- `AGENTS.md`
- `MVP_SCOPE.md`
- `TECH_STACK.md`

Read these only when relevant:

- `README.md` and `PROJECT_BRIEF.md` for product context or unclear requirements.
- `ROADMAP.md` for phase planning, prioritization, or "what next" questions.
- `MVP_IMPLEMENTATION_TRACKER.md` for current implementation status, blockers, next queue, and Jira-style project management.
- `API_BLUEPRINT.md` for endpoint shape, request/response contracts, and API naming.
- `DATABASE_BLUEPRINT.md` for models, relationships, migrations, or schema changes.
- `PERMISSIONS_MATRIX.md` for role access, ownership checks, or protected endpoints.
- `UI_DESIGN_SYSTEM.md` for admin/mobile UI layout, styling, states, and component behavior.
- `CODEX_INSTRUCTIONS.md` only when the task needs the full agent workflow rules or there is conflict between docs.

If a doc is large, scan headings first and read only the relevant section.

## App Routing

Choose the target app before inspecting code:

- Backend API: `apps/backend`
- Admin dashboard: `apps/admin`
- Mobile app: `apps/mobile-ui-lab`

Do not recreate or use `apps/mobile` unless the user explicitly asks.

## Implementation Rules

- Continue the existing architecture; do not rebuild or switch frameworks.
- Keep work MVP-only unless the user explicitly asks for future features.
- Backend must enforce permissions and ownership checks; never rely on frontend-only validation.
- Use exact status values from `MVP_SCOPE.md`.
- For admin UI, use shadcn/ui as the required component library.
- Reuse `apps/admin/src/components/ui/*`; add missing admin primitives from `apps/admin` with `npx shadcn@latest add <component>`.
- Do not hand-build admin buttons, inputs, selects, dialogs, tables, badges, cards, forms, tooltips, or confirmation modals when shadcn/ui can provide them.
- Update `MVP_IMPLEMENTATION_TRACKER.md` when implementation status, blockers, or next tasks change.

## Before Editing

State in one sentence: docs read, target app/file, change being made, what is out of scope.

## Memory Update

After completing any task, silently check if any new stable facts were discovered (new patterns, fixed bugs, architectural decisions, known gaps). If yes, update `.claude/PROJECT_MEMORY.md` without announcing it.

Do not update for things already there, temporary findings, or anything likely to change next session.

## Verification

Run the smallest useful check:

- Backend: targeted pytest
- Admin: lint/build when practical
- Mobile: TypeScript/start check when practical

If a check is skipped or fails for environment reasons, say so clearly.
