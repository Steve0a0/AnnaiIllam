# Product

## Register

product

<!-- Register override per surface:
     - Admin dashboard (web): product
     - Worker mobile app: product
     - Client mobile app: brand (override with $impeccable --register brand when working on client surfaces)
-->

## Users

**Operations staff (admin web)** — Annai Illam employees managing the full staffing lifecycle.
Power users, desktop, working across multiple open tabs. Primary job: match workers to
requirements, resolve exceptions, track attendance, process payroll. They scan tables and
status badges more than they read prose. Speed and information density matter.

**Client companies (client mobile app)** — business owners, HR managers, and site supervisors
at companies that hire contract labour. Used on iOS/Android, typically during office hours.
Primary job: raise a staffing requirement, approve a quote, track who is on-site today.
They see Annai Illam as a service vendor — the app is the face of that relationship. Trust
and polish matter as much as function.

**Deployed workers (worker mobile app)** — field staff checking in and out of job sites,
viewing their schedule, and checking payment status. Used outdoors on low-end Android
(2 GB RAM), often in bright sunlight. Many have low digital literacy. Primary job: check in,
check out, see the next shift. One job. One button. Nothing else should compete for attention.

## Product Purpose

Annai Illam is a B2B manpower staffing platform for the Indian market. It connects companies
that need contract workers with a managed pool of deployed staff, and gives the operations
team the tools to run the entire pipeline: requirement intake, worker assignment, GPS-verified
attendance, dispute resolution, and payroll.

Success looks like: a site supervisor checks in without confusion, an admin assigns 40 workers
in under two minutes, and a client company re-orders because the platform felt reliable.

## Brand Personality

Trustworthy, efficient, professional.

The brand is not warm or friendly — it is steady and competent. The kind of platform a
factory owner in Coimbatore or a logistics manager in Chennai would trust with their payroll.
Quiet authority, not startup energy.

## Anti-references

- Generic purple-gradient SaaS templates (Linear, Vercel, Notion aesthetic)
- Glassmorphism dark mode with neon accents
- Overly animated consumer apps (Swiggy, Zomato energy on a staffing tool)
- Cluttered Bootstrap-style admin panels (dense tables, no hierarchy, 12 shades of grey)
- Any design that looks like a free theme or template
- Fintech navy-and-gold "premium" clichés
- Consumer-app rounded everything (32px+ card radii, pill inputs)

## Design Principles

1. **Status before detail.** Every record shows its status badge immediately. Operations staff
   make decisions from the list view, not the detail page. Status is the primary signal.

2. **One surface, one register.** The admin is a control room: dense, scannable, no decoration.
   The client app is a boardroom in your pocket: clean, premium, trustworthy. The worker app
   is a physical tool: large targets, maximum contrast, zero cognitive load. Each surface is
   designed for its specific user, not for a unified aesthetic.

3. **No serif anywhere. One sans-serif family throughout.** Geist across all type roles:
   headings, labels, body, and data. Hierarchy through weight (400 body, 500 labels, 600
   headings, 700 display numbers) and size, not through font mixing. Operational trust over
   editorial personality: this platform is used by field workers and ops managers, not creative
   professionals. Legibility at small sizes and on low-end Android screens takes priority over
   any typographic character.

4. **Contrast is a non-negotiable for the worker app.** Workers check in outdoors in direct
   sunlight on budget screens. WCAG AA is the minimum; AAA is the target on the worker surface.
   Large type (16px minimum body), no muted-gray anything, no low-contrast secondary text.
   Placeholder text meets the same 4.5:1 minimum as body text — no exceptions.

5. **Restraint earns trust.** No decorative gradients, no illustrations, no personality quirks.
   Brand credibility is built through consistency, precision, and the absence of visual noise.
   Every element that cannot justify its presence should be removed.

6. **Clarity over cleverness in copy.** Labels, button text, and error messages are written for
   a factory worker or a non-technical HR manager, not for a product designer. Verb + object
   on every button. Specific consequences in every confirmation. No buzzwords.

## Accessibility & Inclusion

- **Admin web:** WCAG 2.1 AA minimum. Full keyboard navigation. Skip-to-content link.
  Screen reader support on all data tables and interactive elements.
- **Client mobile:** WCAG 2.1 AA. Standard accessible touch targets (44pt minimum).
- **Worker mobile:** WCAG 2.1 AAA target on all primary UI. Minimum 16px body type.
  Minimum 56px touch targets for all primary actions. No information conveyed by color alone.
  Icons must be universally legible without reading the label (universal iconography, no
  abstract metaphors). Support for Android accessibility services (TalkBack).
- All animation wrapped in `@media (prefers-reduced-motion)`. No information lost when
  motion is disabled.
