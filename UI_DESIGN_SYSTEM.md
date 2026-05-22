# UI Design System — Annai Illam Staffing Platform
# Production-Grade · Version 1.0

---

## Design Direction

**Aesthetic:** Refined industrial — the visual language of serious operations software.
Clean, authoritative, and quietly premium. Not sterile SaaS. Not cluttered enterprise.
The kind of tool that makes a site supervisor or HR manager feel in control.

**What makes this system unforgettable:**
- A deep forest green that reads as ownership, not decoration
- Typography that switches between serif authority and sans-serif clarity
- Every status is colour-coded with semantic precision — users build muscle memory
- The worker app is so stripped back it feels like hardware, not software

**Three surfaces, one language:**
- Admin web: dense, scannable, powerful — a control room
- Client mobile: professional, reassuring — a boardroom in your pocket
- Worker mobile: brutally simple — one job, one button, nothing else

---

## 1. Brand Tokens

### Color System

All colors are defined as CSS variables (admin) or Tamagui tokens (mobile).
Use token names in code. Never hardcode hex values directly.

#### Primary Palette

```
--color-brand-900:    #0D2E1E   Darkest — sidebar bg, deep surfaces
--color-brand-800:    #113D28   Dark surface backgrounds
--color-brand-700:    #165233   Primary action bg (hover)
--color-brand-600:    #1A6640   Primary — buttons, active nav, key icons
--color-brand-500:    #1D7A4A   Slightly lighter primary
--color-brand-400:    #25A263   Hover accent
--color-brand-300:    #4DBF87   Lighter accent, icon tint on dark bg
--color-brand-200:    #A8DFBF   Tint background
--color-brand-100:    #D4F0E3   Very light tint, selected states
--color-brand-50:     #EDFAF3   Lightest — hover bg, active card bg
```

#### Neutral Palette (Warm — not cold grey)

```
--color-neutral-950:  #0C0A09   True black
--color-neutral-900:  #1C1917   Near-black — primary headings
--color-neutral-800:  #292524   Dark body text
--color-neutral-700:  #44403C   Body text
--color-neutral-600:  #57534E   Secondary text
--color-neutral-500:  #78716C   Muted text, placeholders
--color-neutral-400:  #A8A29E   Disabled text, hints
--color-neutral-300:  #D6D3D1   Borders, dividers
--color-neutral-200:  #E7E5E4   Subtle borders
--color-neutral-100:  #F5F5F4   Page background
--color-neutral-50:   #FAFAF9   Card background (warm off-white)
--color-white:        #FFFFFF   Input bg, pure white surfaces
```

#### Semantic Palette

```
Success
--color-success-700:  #15803D
--color-success-500:  #22C55E
--color-success-100:  #DCFCE7
--color-success-50:   #F0FDF4

Warning
--color-warning-700:  #B45309
--color-warning-500:  #F59E0B
--color-warning-100:  #FEF3C7
--color-warning-50:   #FFFBEB

Danger
--color-danger-700:   #B91C1C
--color-danger-500:   #EF4444
--color-danger-100:   #FEE2E2
--color-danger-50:    #FFF1F2

Info
--color-info-700:     #1D4ED8
--color-info-500:     #3B82F6
--color-info-100:     #DBEAFE
--color-info-50:      #EFF6FF

Purple (Under Review / In Review)
--color-purple-700:   #6D28D9
--color-purple-500:   #8B5CF6
--color-purple-100:   #EDE9FE
--color-purple-50:    #F5F3FF

Teal (In Progress / Checked In)
--color-teal-700:     #0E7490
--color-teal-500:     #06B6D4
--color-teal-100:     #CFFAFE
--color-teal-50:      #ECFEFF
```

#### Surface Tokens

```
Admin web:
  --surface-page:          #F5F5F4
  --surface-card:          #FFFFFF
  --surface-sidebar:       #0D2E1E
  --surface-sidebar-hover: #1A4A2A
  --surface-elevated:      #FFFFFF
  --surface-subtle:        #FAFAF9

Mobile:
  --surface-page-mobile:   #F5F5F4
  --surface-card-mobile:   #FFFFFF
  --surface-bottom-bar:    #FFFFFF
```

---

## 2. Typography

### Font Stack

```
Display:    'Fraunces', serif
            Used for: Large headings, dashboard numbers, modal titles
            Weights:  400 (regular), 600 (semibold)
            Note:     Italic variant used for editorial emphasis

UI / Body:  'Geist', sans-serif
            Used for: All interface text, labels, buttons, body copy
            Weights:  300 (light), 400 (regular), 500 (medium)

Mono:       'Geist Mono', monospace
            Used for: Amounts, timestamps, ID codes, invoice numbers
            Weights:  400, 500
```

### Font Installation

```
Admin (Next.js — use next/font/google):
  Fraunces:  weights 400, 600
  Geist:     weights 300, 400, 500
  Geist Mono: weights 400, 500

Mobile (Expo):
  @expo-google-fonts/fraunces
  @expo-google-fonts/geist
  (Geist Mono via @expo-google-fonts/geist-mono)
```

### Type Scale

```
NAME          SIZE    LINE-H   WEIGHT   TRACKING   USE
────────────────────────────────────────────────────────────────────
display-xl    48px    1.1      600      -0.03em    Dashboard hero numbers
display-lg    36px    1.15     600      -0.025em   Large KPI numbers
display-md    28px    1.2      600      -0.02em    Modal titles, page headers
heading-xl    24px    1.25     500      -0.015em   Page titles
heading-lg    20px    1.3      500      -0.01em    Card titles, panel headers
heading-md    18px    1.35     500      -0.01em    Section titles
heading-sm    16px    1.4      500      -0.005em   Subsection titles
body-lg       15px    1.6      400      0          Primary body text
body-md       14px    1.6      400      0          Secondary body, table rows
body-sm       13px    1.55     400      0          Captions, helper text
label-lg      13px    1.0      500      0.02em     Form labels, table headers
label-md      12px    1.0      500      0.02em     Tags, small labels
label-sm      11px    1.0      500      0.04em     Eyebrows, micro-labels (ALL CAPS)
mono-lg       14px    1.5      500      -0.01em    Amounts, important codes
mono-md       13px    1.5      400      -0.01em    Timestamps, IDs
mono-sm       12px    1.5      400      0          Small codes
```

### Typography Rules

```
1. Fraunces is used ONLY for:
   - Page headings and modal primary titles
   - Large KPI and stat numbers
   - Do NOT use for body text, labels, or buttons

2. Geist covers everything else:
   - Navigation labels, button text, form labels, body copy
   - Table content, helper text, placeholders

3. Geist Mono covers:
   - All currency amounts (₹18,400)
   - Date and time values (06:00 – 14:00)
   - Reference codes and IDs (INV-0042)
   - Any stat number inside a KPI card

4. Maximum font weights in use: 300, 400, 500
   Never use 600+ for Geist (only Fraunces uses 600)

5. ALL CAPS is permitted only for label-sm eyebrow text
   Examples: "TODAY'S SHIFT", "ACTIVE JOBS", "THIS WEEK"

6. Tracking widens on small labels, tightens on large display
```

---

## 3. Spacing System

Base unit: **4px**

```
TOKEN     VALUE   USE
────────────────────────────────────────────────────────
space-1   4px     Tight internal gaps (icon + label gap)
space-2   8px     Between related items, tag gaps
space-3   12px    Compact component padding
space-4   16px    Standard component padding
space-5   20px    Card padding (mobile)
space-6   24px    Card padding (desktop), small section gap
space-8   32px    Medium section gap, page padding (desktop)
space-10  40px    Large section gap
space-12  48px    Major section separator
space-16  64px    Page section gap
space-20  80px    Hero section padding
```

### Fixed Component Measurements

```
Card padding:              20px mobile / 24px desktop
Table cell padding:        12px 16px
Input height:              44px desktop / 52px mobile
Input padding:             10px 14px
Button height:             44px desktop / 52px mobile
Button padding:            0 24px
Mobile primary CTA height: 56px
Modal padding:             32px
Sidebar width:             240px (desktop)
Top bar height:            56px
Bottom tab bar height:     64px + safeAreaInsets.bottom
Page horizontal padding:   16px mobile / 32px desktop
```

---

## 4. Border and Radius

### Radius Tokens

```
radius-sm:    4px     Badges, tags, small chips
radius-md:    8px     Inputs, buttons, small cards
radius-lg:    12px    Standard cards, panels
radius-xl:    16px    Large cards, modals
radius-2xl:   24px    Hero cards on mobile (worker dashboard)
radius-full:  9999px  Pill badges, avatars, toggles
```

### Border Tokens

```
border-subtle:  1px solid #E7E5E4   Default card borders
border-default: 1px solid #D6D3D1   Inputs (unfocused)
border-strong:  1px solid #A8A29E   Dividers with more emphasis
border-brand:   1px solid #1A6640   Selected / active state
border-focus:   2px solid #1A6640   Focus ring base
```

### Focus Ring

```css
/* Applied to all interactive elements on :focus-visible */
outline: none;
box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #1A6640;
```

---

## 5. Shadow System

```
shadow-xs:    0 1px 2px rgba(0,0,0,0.04)
              Use: Extremely subtle lift

shadow-sm:    0 1px 3px rgba(0,0,0,0.06),
              0 1px 2px rgba(0,0,0,0.04)
              Use: Standard cards

shadow-md:    0 4px 6px rgba(0,0,0,0.05),
              0 2px 4px rgba(0,0,0,0.04)
              Use: Elevated cards, hover state

shadow-lg:    0 10px 15px rgba(0,0,0,0.07),
              0 4px 6px rgba(0,0,0,0.04)
              Use: Dropdowns, popovers

shadow-xl:    0 20px 25px rgba(0,0,0,0.08),
              0 8px 10px rgba(0,0,0,0.04)
              Use: Modals

shadow-brand: 0 4px 14px rgba(26,102,64,0.25)
              Use: Primary button hover, check-in button
```

---

## 6. Component Specifications

### 6.1 Buttons

#### Primary Button

```
Height:         44px desktop / 52px mobile
Padding:        0 24px
Background:     #1A6640 (--color-brand-600)
Text:           White, Geist 14px 500
Border:         None
Radius:         radius-md (8px)
Icon:           16px icon, 8px gap

States:
  Default:      bg #1A6640
  Hover:        bg #165233 + shadow-brand
  Active:       bg #113D28 + scale(0.98)
  Disabled:     bg #A8A29E, opacity 0.5, cursor not-allowed
  Loading:      20px spinner replaces label, bg unchanged
```

#### Secondary Button (Outline)

```
Height:         44px desktop / 52px mobile
Padding:        0 24px
Background:     Transparent
Border:         1.5px solid #1A6640
Text:           #1A6640, Geist 14px 500
Radius:         radius-md (8px)

States:
  Hover:        bg --color-brand-50
  Active:       bg --color-brand-100
  Disabled:     border #D6D3D1, text #A8A29E
```

#### Ghost Button

```
Height:         44px desktop / 48px mobile
Background:     Transparent
Border:         None
Text:           #57534E, Geist 14px 400
Radius:         radius-md

States:
  Hover:        bg --color-neutral-100
  Active:       bg --color-neutral-200
```

#### Destructive Button

```
Background:     #EF4444
Text:           White, Geist 14px 500
Height:         44px
Radius:         radius-md
Rule:           Used ONLY inside confirmation modals
                NEVER as a default page action
```

#### Mobile Full-Width Primary CTA

```
Width:          100% (with 16px horizontal margin on each side)
Height:         56px
Position:       Fixed at bottom, 16px above tab bar
                paddingBottom: safeAreaInsets.bottom + 16px
Radius:         14px
Shadow:         shadow-brand
Font:           Geist 15px 500
Text:           White
```

---

### 6.2 Input Fields and Forms

#### Text Input

```
Height:         44px desktop / 52px mobile
Padding:        10px 14px
Background:     #FFFFFF
Border:         border-default (1px solid #D6D3D1)
Radius:         radius-md (8px)
Font:           Geist body-md (14px 400)
Text color:     --color-neutral-900
Placeholder:    Geist 14px 400, #A8A29E

States:
  Focus:        border-brand + focus ring
  Error:        Border #EF4444 + ring rgba(239,68,68,0.15)
  Disabled:     bg #F5F5F4, text #A8A29E, cursor not-allowed
  Filled:       border-default (no visual change needed)
```

#### Form Label

```
Font:           Geist label-lg (13px 500)
Color:          #44403C
Margin-bottom:  6px
Required:       Asterisk (*) in #EF4444, 4px left margin
```

#### Helper / Error / Success Text

```
Font:           Geist body-sm (13px 400)
Margin-top:     5px
Position:       Below input field, always in DOM (not tooltip)

Success:        #15803D
Error:          #B91C1C
Neutral:        #78716C
```

#### Step-by-Step Wizard Form (Job Request Creation)

```
Progress bar:
  Height:       3px
  Background:   #E7E5E4
  Fill:         #1A6640
  Radius:       radius-full
  Transition:   width 0.3s ease

Step indicator:
  Font:         Geist label-sm (11px 500 UPPERCASE)
  Color:        #78716C
  Text:         "STEP 2 OF 4"

Step content:
  Max 4 fields per step
  Step title: heading-sm (16px 500, Geist)
  Back button: Ghost (left)
  Next button: Primary (right)
  Save Draft:  Available from any step
```

---

### 6.3 Cards

#### Standard Card

```
Background:     #FFFFFF
Border:         1px solid #E7E5E4
Radius:         radius-lg (12px)
Padding:        20px mobile / 24px desktop
Shadow:         shadow-sm
Hover:          shadow-md + border #D6D3D1 (on clickable cards)
Transition:     box-shadow 0.15s ease, border-color 0.15s ease
```

#### KPI / Stat Card (Admin Dashboard)

```
Background:     #FFFFFF
Border:         1px solid #E7E5E4
Radius:         radius-lg (12px)
Padding:        20px 24px
Shadow:         shadow-sm

Layout (top to bottom):
  Row 1:    Icon container (40×40px, radius-md, tinted bg)
            + Trend badge (right-aligned)
  Row 2:    display-lg number (Fraunces 36px 600)
  Row 3:    label-md description + secondary comparison text

Icon container background:
  Green metrics:    --color-brand-50
  Warning metrics:  --color-warning-50
  Danger metrics:   --color-danger-50
  Info metrics:     --color-info-50
```

#### Job Request Card (Client Mobile)

```
Background:     #FFFFFF
Border:         1px solid #E7E5E4 (default) / 1.5px solid #1A6640 (active)
Radius:         16px
Padding:        20px
Shadow:         shadow-sm

Layout:
  Top row:      Job title (heading-sm) + Status badge (right)
  Mid row:      Location text + date range (body-sm, #78716C)
  Bottom row:   Worker count chip + Shift chip (left) + Arrow (right)
```

#### Worker Hero Card (Worker Dashboard — most important element)

```
Background:     #0D2E1E (--color-brand-900)
Radius:         24px
Padding:        24px
Text:           White on dark

Layout:
  Eyebrow:      "TODAY'S SHIFT" label-sm, rgba(white,0.45), tracking 0.08em
  Company:      heading-lg (20px 500), white
  Location:     body-sm, rgba(white,0.65) + pin icon 14px
  Shift time:   mono-lg (14px 500), white + clock icon 14px
  Separator:    1px solid rgba(255,255,255,0.10)
  CTA button:   (see check-in button spec)
```

#### Alert / Notice Card

```
Border-left:    3px solid (matching semantic colour)
Radius:         0 8px 8px 0
Background:     matching -50 tint
Padding:        12px 16px
Layout:         16px icon + text, flex row, gap 10px
```

---

### 6.4 Status Badges

All badges: Geist 12px 500, padding 4px 10px, radius-full (pill), height 22px

```
STATUS              BACKGROUND        TEXT COLOUR
────────────────────────────────────────────────────────────
DRAFT               #F5F5F4           #78716C
SUBMITTED           #DBEAFE           #1D4ED8
UNDER_REVIEW        #EDE9FE           #6D28D9
APPROVED            #DCFCE7           #15803D
WORKERS_ASSIGNED    #D1FAE5           #065F46
IN_PROGRESS         #CFFAFE           #0E7490
COMPLETED           #DCFCE7           #15803D
CANCELLED           #FEE2E2           #B91C1C
REJECTED            #FEE2E2           #B91C1C

ASSIGNED            #DBEAFE           #1D4ED8
ACCEPTED            #DCFCE7           #15803D
DECLINED            #FEE2E2           #B91C1C
REPLACED            #FEF3C7           #B45309

NOT_STARTED         #F5F5F4           #78716C
CHECKED_IN          #CFFAFE           #0E7490
CHECKED_OUT         #DBEAFE           #1D4ED8
VERIFIED            #DCFCE7           #15803D
ABSENT              #FEE2E2           #B91C1C
LATE                #FEF3C7           #B45309

OPEN                #DBEAFE           #1D4ED8
IN_REVIEW           #EDE9FE           #6D28D9
RESOLVED            #DCFCE7           #15803D

PENDING             #FEF3C7           #B45309
PAID                #DCFCE7           #15803D
OVERDUE             #FEE2E2           #B91C1C
────────────────────────────────────────────────────────────
```

Optional leading dot: 6px circle, same colour as text, 6px right margin.
Pulsing dot animation: CHECKED_IN and IN_PROGRESS only (CSS keyframe opacity pulse).

---

### 6.5 Data Tables (Admin)

```
Table wrapper:
  Background:   #FFFFFF
  Border:       1px solid #E7E5E4
  Radius:       12px
  Overflow:     hidden

Table header row:
  Background:   #FAFAF9
  Border-bottom: 1px solid #E7E5E4
  Height:       44px
  Font:         Geist label-lg (13px 500)
  Color:        #78716C
  Padding:      12px 16px
  Sort icon:    12px chevron, visible on hover of sortable column

Table body row:
  Height:       56px (compact) / 64px (standard, with avatar)
  Border-bottom: 1px solid #F5F5F4
  Font:         Geist body-md (14px 400)
  Color:        #292524
  Padding:      12px 16px
  Hover:        bg #FAFAF9, cursor pointer

Row actions:
  Visibility:   Hidden by default, shown on row hover
  Position:     Right side, flex row, gap 4px
  Each:         Icon button 32×32px, ghost style

Last row:
  Border-bottom: None

Pagination footer:
  Height:       52px
  Border-top:   1px solid #E7E5E4
  Padding:      0 16px
  Left:         "Showing 1–20 of 124" Geist body-sm #78716C
  Right:        Page buttons 32×32px radius-md
  Active page:  bg #1A6640, text white
  Other pages:  Ghost style
```

---

### 6.6 Navigation

#### Admin Sidebar

```
Width:          240px
Background:     #0D2E1E
Height:         100vh, fixed position
Padding:        0

Logo area:
  Height:       64px
  Padding:      0 20px
  Content:      Logo mark (32px) + "Annai Illam" Fraunces 16px white

Section label:
  Font:         Geist label-sm (11px 500 UPPERCASE)
  Color:        rgba(255,255,255,0.30)
  Padding:      20px 20px 8px

Nav item:
  Height:       44px
  Margin:       0 8px
  Padding:      0 12px
  Radius:       radius-md (8px)
  Font:         Geist body-md (14px 400)
  Color:        rgba(255,255,255,0.60)
  Icon:         20px, same colour
  Gap:          10px between icon and label

  Hover:        bg rgba(255,255,255,0.06), color rgba(white,0.85)
  Active:       bg #1A6640, color white, icon white

  Count badge:  Right-aligned pill
                bg rgba(255,255,255,0.12), text white
                Radius-full, height 18px, padding 0 8px

Bottom:
  Profile block: Avatar 32px + Name body-sm + Role label-sm
                 Pinned to bottom, padding 16px 12px
  Separator:    1px solid rgba(255,255,255,0.08)
```

#### Admin Top Bar

```
Height:         56px
Background:     #FFFFFF
Border-bottom:  1px solid #E7E5E4
Padding:        0 32px
Layout:         [Page title] [spacer] [Search] [Notifications] [Avatar]

Page title:     Fraunces 20px 500, #1C1917

Search:
  Width:        280px
  Height:       36px
  Background:   #F5F5F4
  Border:       None
  Radius:       8px
  Placeholder:  "Search..."
  Focus:        bg white + border-brand + shadow-sm

Notifications:
  Icon:         Bell, 22px, #78716C
  Unread dot:   8px circle, #EF4444, top-right of icon

Avatar:
  Size:         36px circle
  Initials:     Geist 13px 500, white
  Background:   #1A6640
  Border:       2px solid #D4F0E3
```

#### Mobile Bottom Tab Bar

```
Height:         64px + safeAreaInsets.bottom
Background:     #FFFFFF
Border-top:     1px solid #E7E5E4
Shadow:         0 -4px 12px rgba(0,0,0,0.06)

Tab item:
  Flex:         1 (equal width)
  Layout:       Icon centered top + label below
  Icon:         24px
  Label:        Geist 11px 500
  Gap:          3px between icon and label

  Default:      Icon + label #A8A29E
  Active:       Icon + label #1A6640
  Active dot:   2px × 2px dot below icon, #1A6640

Worker tabs:    Home | My Jobs | Attendance | Profile
Client tabs:    Home | Requests | Workers | Profile
```

---

### 6.7 Modals and Bottom Sheets

#### Desktop Modal

```
Overlay:        rgba(0, 0, 0, 0.45)
Animation:      scale(0.96) opacity(0) → scale(1) opacity(1), 180ms ease-out

Container:
  Background:   #FFFFFF
  Radius:       16px
  Shadow:       shadow-xl
  Width:        480px standard / 640px wide (assign workers)
  Padding:      32px

Header:
  Title:        Fraunces 24px 600, #1C1917
  Close:        32×32 icon button, top-right corner
  Separator:    None — bottom padding creates visual gap

Footer:
  Margin-top:   24px
  Alignment:    Right
  Gap:          12px
  Buttons:      Ghost "Cancel" + Primary/Destructive "Confirm"
```

#### Mobile Bottom Sheet

```
Background:     #FFFFFF
Radius:         24px 24px 0 0
Shadow:         0 -8px 32px rgba(0,0,0,0.12)
Handle:         32px wide × 4px tall, #D6D3D1, centered, 12px from top
Padding:        8px 24px 24px + safeAreaInsets.bottom
Animation:      translateY(100%) → translateY(0), 280ms spring
Dismiss:        Drag down past 40% of sheet height
```

---

### 6.8 Empty States

Every list and data container must have a designed empty state — never a blank area.

```
Layout:         Vertically and horizontally centered
Padding:        40px 24px

Icon:           48px, #D6D3D1 (outline SVG, not filled)
Title:          Fraunces 16px 400, #44403C
Description:    Geist body-sm 13px, #78716C, max-width 260px, centered
Action:         Optional Primary button, margin-top 20px

Examples:

  No job requests (admin):
    Icon:       clipboard
    Title:      "No requests yet"
    Body:       "New requests from clients will appear here."

  No workers found (filter active):
    Icon:       search / person
    Title:      "No workers match your filters"
    Body:       "Try adjusting your search or removing filters."
    Action:     [Clear filters]

  No complaints:
    Icon:       check circle
    Title:      "All clear"
    Body:       "No complaints have been raised."
    (No action — this is good news)

  No notifications:
    Icon:       bell
    Title:      "You're all caught up"
    Body:       "New notifications will appear here."
```

---

### 6.9 Loading States

```
Skeleton loader:
  Background:     #F5F5F4
  Shimmer:        Animated gradient moves left-to-right, 1.5s ease infinite
  Radius:         Matches the element (text = radius-sm, card = radius-lg)
  Delay:          Only show after 200ms (prevents flicker on fast loads)
  Rule:           ALWAYS use skeletons for page-level data loading
                  NEVER show blank space while loading

Inline spinner (in buttons, small inline):
  Size:           20px (button) / 24px (standalone)
  Colour:         Inherits text colour
  Animation:      Rotate 360deg, 0.65s linear infinite

Page transition:
  Enter:          opacity 0 → 1, 150ms ease
  Exit:           opacity 1 → 0, 100ms ease
```

---

### 6.10 Toast Notifications

```
Position:       Top-right (desktop) / Top-center (mobile)
Width:          360px max desktop / calc(100% - 32px) mobile
Background:     #1C1917 (near-black — stands out on any bg)
Text:           White, Geist body-sm
Radius:         10px
Shadow:         shadow-lg
Padding:        14px 16px
Layout:         [20px icon] [flex text] [optional action] [× close]
Auto-dismiss:   4s success/info / 7s error
Animation:      Slide down + fade from top, spring 280ms

Left border variants:
  Success:   3px solid #22C55E + check icon
  Error:     3px solid #EF4444 + alert circle icon
  Warning:   3px solid #F59E0B + warning icon
  Info:      3px solid #25A263 + info icon
```

---

### 6.11 Confirmation Modals

Required before any of these actions:
- Approve or reject a job request
- Assign workers (sends notifications)
- Deactivate a client or worker
- Resolve or reject a complaint
- Any action that cannot be undone

```
Title:        Spell out what is happening, not "Are you sure?"
              Good: "Reject this job request?"
              Bad:  "Confirm action"

Body:         One sentence explaining the consequence
              "The client will be notified that their request has been rejected."

Input:        Text field if reason is required (rejection, resolution)

Buttons:      Ghost "Cancel" + Primary or Destructive "Confirm [action]"
              Button label matches the action: "Reject Request", "Deactivate Worker"
```

---

## 7. Admin Dashboard Layout

### Full Page Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ SIDEBAR — 240px, fixed, full height                                  │
│  Logo area (64px)                                                    │
│  Nav section: Operations                                             │
│    Dashboard / Requests / Workers / Clients / Attendance             │
│  Nav section: Management                                             │
│    Complaints / Settings                                             │
│  Profile block (bottom, pinned)                                      │
├─────────────────────────────────────────────────────────────────────┤
│ CONTENT AREA — calc(100vw - 240px)                                   │
│                                                                      │
│  TOP BAR — 56px, sticky                                              │
│  [Page title]         [Search bar]  [Bell]  [Avatar]                 │
│  ──────────────────────────────────────────────────────────────────  │
│                                                                      │
│  PAGE CONTENT — padding 32px                                         │
│                                                                      │
│  KPI ROW (5 stat cards, equal width grid)                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │ Req  │ │ Jobs │ │ Work │ │ Att  │ │Compl │                      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                      │
│                                                                      │
│  MAIN CONTENT                                                        │
│  Priority actions list (left, 2/3 width) + Activity feed (1/3)      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### KPI Cards — Dashboard

```
Grid:         grid-template-columns: repeat(5, 1fr), gap 16px
Responsive:   4 cols at 1400px / 3 at 1280px / 2 at 1024px

Card content:
  Row 1:  [Icon in tinted 40×40 box]     [Trend pill — "+12% this week"]
  Row 2:  [Number — Fraunces 36px]
  Row 3:  [Label — "Pending Requests"]   [Delta — "+3 since yesterday"]

Trend pill:
  Positive: bg #DCFCE7, text #15803D, ↑ icon
  Negative: bg #FEE2E2, text #B91C1C, ↓ icon
  Neutral:  bg #F5F5F4, text #78716C, → icon
```

### Detail Page Layout (Job Request Detail)

```
Header:
  Breadcrumb:     "Requests / Job #1042" label-sm #78716C
  Title:          Fraunces 28px 600, job name
  Meta row:       [Client badge] [Location] [Date range] — body-sm #78716C
  Actions:        Right-aligned: [Reject] [Approve] or [Assign Workers]
  Border-bottom:  1px solid #E7E5E4, margin-bottom 24px

Content grid: 2-column, 2:1 ratio, gap 24px

Left (main area):
  Request info card
  Assigned workers list
  Attendance summary

Right (sidebar):
  Status timeline card
  Quick info summary
  Related items

Status timeline:
  Vertical line:    2px #E7E5E4
  Completed node:   12px circle #1A6640
  Current node:     12px circle #1A6640, pulsing ring
  Future node:      12px circle #D6D3D1
  Label:            body-sm + mono-sm timestamp
```

---

## 8. Client Mobile Layout

### Screen Structure (All Client Screens)

```
┌─────────────────────────────┐
│  STATUS BAR (system, 44pt)  │
├─────────────────────────────┤
│  HEADER (56px)              │
│  Back arrow (if needed)     │
│  Title: heading-lg Fraunces │
│  Right: action icon button  │
├─────────────────────────────┤
│                             │
│  SCROLLABLE CONTENT         │
│  paddingHorizontal: 16      │
│  paddingTop: 16             │
│                             │
├─────────────────────────────┤
│  PRIMARY CTA (when needed)  │
│  56px, fixed bottom         │
├─────────────────────────────┤
│  BOTTOM TAB BAR (64px)      │
│  + safe area                │
└─────────────────────────────┘
```

### Client Dashboard Scroll Layout

```
Greeting:
  "Good morning, [First Name]"   Fraunces heading-lg italic
  "Tuesday, 5 May"                Geist body-sm #78716C

Active Jobs section:
  Label: "ACTIVE JOBS"            label-sm UPPERCASE #78716C, mb 10px
  Horizontal scroll:              Job Request Cards (88vw each, gap 12px)
  Peek:                           Next card visible at right edge (shows more content)

Quick Stats row (3 cards equal width):
  Workers on site today
  Open requests
  Pending complaints

Recent Activity:
  Label: "RECENT ACTIVITY"
  List items:
    Left: 36px tinted icon circle + text (heading bold action + sub description)
    Right: mono-sm timestamp
    Divider: 1px #F5F5F4
```

---

## 9. Worker Mobile Layout

### Worker Dashboard — Full Production Spec

```
Screen bg:    #F5F5F4

─── Greeting bar (56px) ───────────────────────────────────────────
  paddingHorizontal: 20
  Left:  "Today" label-sm #78716C / date mono-sm #44403C
  Right: Bell icon button (notification count badge)

─── Hero Job Card ─────────────────────────────────────────────────
  Margin: 16px horizontal
  Background: #0D2E1E
  Radius: 24px
  Padding: 24px

  "TODAY'S SHIFT"     label-sm, rgba(255,255,255,0.40), tracking 0.08em
  [Company Name]      heading-lg (20px 500), white
  [Pin] [Location]    body-sm, rgba(255,255,255,0.60)
  [Clock] [06:00–14:00]  mono-lg (14px 500), white

  ── separator: 1px rgba(255,255,255,0.10), my 16px ──

  CHECK IN BUTTON:
    Height: 56px
    Width: 100%
    Radius: 14px
    Background: #25A263 (brand-400)
    Text: "Check In" Geist 16px 500 white
    Icon: location pin 18px white

    CHECKED IN state:
      Background: rgba(255,255,255,0.10)
      Border: 1px solid rgba(255,255,255,0.15)
      Left: Green pulse dot 8px + "Checked in at 06:02" body-sm white
      Right: "Check Out" ghost button style

  No job today state:
    Show empty state inside card:
      Icon: calendar outline, rgba(white,0.25)
      Text: "No shift today" heading-sm rgba(white,0.60)
      Sub:  "Enjoy your day off" body-sm rgba(white,0.35)

─── This Week ─────────────────────────────────────────────────────
  Label: "THIS WEEK"  label-sm #78716C, margin 20px 16px 10px
  Row of 5 day tiles: margin 0 16px, gap 8px

  Each tile:
    Width: (screen - 32px - 4*8px) / 5
    Height: 60px
    Radius: 10px
    Layout: Day initial (label-sm) above / Date number (heading-sm)

    Present:  bg #D4F0E3, text #165233
    Absent:   bg #FEE2E2, text #B91C1C
    Late:     bg #FEF3C7, text #B45309
    Today:    bg #1A6640, text white
    Future:   bg #E7E5E4, text #A8A29E

─── Next Payment ──────────────────────────────────────────────────
  Standard card, margin 0 16px
  Left:  "NEXT PAYMENT" label-sm #78716C / date body-sm #44403C
  Right: "₹18,400" mono-lg #1A6640 font-500

─── Bottom padding ────────────────────────────────────────────────
  paddingBottom: tabBarHeight + 16px
```

---

## 10. Interaction and Animation

### Timing Defaults

```css
/* Standard UI interaction */
transition: all 0.15s ease;

/* Card hover */
transition: box-shadow 0.2s ease, border-color 0.15s ease;

/* Button press */
transition: transform 0.1s ease, background-color 0.12s ease;

/* Modal enter */
animation: modalIn 0.18s cubic-bezier(0.16, 1, 0.3, 1) forwards;

/* Sheet enter (mobile) */
animation: sheetIn 0.28s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;

/* Toast enter */
animation: toastIn 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
```

### Keyframes

```css
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(4px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes sheetIn {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}

@keyframes toastIn {
  from { opacity: 0; transform: translateY(-12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
  from { background-position: -400px 0; }
  to   { background-position: 400px 0; }
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.75); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
```

### Micro-Interaction Rules

```
Button press:         scale(0.97), 100ms
Card tap (mobile):    scale(0.98), 80ms, then navigate
Check-in success:     Button bg pulse green → white → green, 600ms
Status badge appear:  fadeIn 200ms + translateY(2px) → 0
Skeleton → content:   fadeIn 200ms + translateY(4px) → 0
Tab activate:         Icon scale 1 → 1.12 → 1, 200ms ease
Row hover (desktop):  bg transition 150ms ease
```

### Mobile Gesture Rules

```
Swipe right:    Back navigation (native stack behaviour)
Swipe down:     Dismiss bottom sheet
Pull down:      Pull-to-refresh on all list screens
Long press:     NOT used — not discoverable for non-technical users
Swipe left row: Only for single obvious action (e.g. decline on My Jobs)
```

---

## 11. Tamagui Token Config

Complete config for `apps/mobile-ui-lab/tamagui.config.ts`:

```typescript
export const tokens = createTokens({
  color: {
    // Brand
    brand900: '#0D2E1E', brand800: '#113D28', brand700: '#165233',
    brand600: '#1A6640', brand500: '#1D7A4A', brand400: '#25A263',
    brand300: '#4DBF87', brand200: '#A8DFBF', brand100: '#D4F0E3',
    brand50:  '#EDFAF3',
    // Neutrals
    neutral950: '#0C0A09', neutral900: '#1C1917', neutral800: '#292524',
    neutral700: '#44403C', neutral600: '#57534E', neutral500: '#78716C',
    neutral400: '#A8A29E', neutral300: '#D6D3D1', neutral200: '#E7E5E4',
    neutral100: '#F5F5F4', neutral50: '#FAFAF9', white: '#FFFFFF',
    // Semantic
    success700: '#15803D', success500: '#22C55E',
    success100: '#DCFCE7', success50: '#F0FDF4',
    warning700: '#B45309', warning500: '#F59E0B',
    warning100: '#FEF3C7', warning50: '#FFFBEB',
    danger700:  '#B91C1C', danger500:  '#EF4444',
    danger100:  '#FEE2E2', danger50:   '#FFF1F2',
    info700:    '#1D4ED8', info500:    '#3B82F6',
    info100:    '#DBEAFE', info50:     '#EFF6FF',
    purple700:  '#6D28D9', purple100:  '#EDE9FE',
    teal700:    '#0E7490', teal100:    '#CFFAFE',
  },
  space: {
    1: 4, 2: 8, 3: 12, 4: 16, 5: 20,
    6: 24, 8: 32, 10: 40, 12: 48, 16: 64, 20: 80,
    true: 16,
  },
  size: {
    xs: 28, sm: 36, md: 44, lg: 52, xl: 56, true: 44,
  },
  radius: {
    sm: 4, md: 8, lg: 12, xl: 16, '2xl': 24, full: 9999, true: 8,
  },
})

export const fonts = {
  heading: createFont({
    family: 'Fraunces_400Regular',
    size: { 1: 48, 2: 36, 3: 28, 4: 24, 5: 20, 6: 18, 7: 16, true: 20 },
    lineHeight: { 1: 52, 2: 41, 3: 33, 4: 30, 5: 26, 6: 24, true: 26 },
    weight: { 1: '400', 2: '600', true: '500' },
    letterSpacing: { 1: -1.44, 2: -0.9, 3: -0.56, true: -0.48 },
  }),
  body: createFont({
    family: 'Geist_400Regular',
    size: { 1: 15, 2: 14, 3: 13, 4: 12, 5: 11, true: 14 },
    lineHeight: { 1: 24, 2: 22, 3: 20, 4: 18, 5: 16, true: 22 },
    weight: { 1: '300', 2: '400', 3: '500', true: '400' },
    letterSpacing: { 1: 0, 2: 0, 3: 0.26, 4: 0.26, 5: 0.44, true: 0 },
  }),
  mono: createFont({
    family: 'GeistMono_400Regular',
    size: { 1: 14, 2: 13, 3: 12, true: 13 },
    lineHeight: { 1: 21, 2: 19, 3: 18, true: 19 },
    weight: { 1: '500', 2: '400', true: '400' },
    letterSpacing: { true: -0.13 },
  }),
}

export const themes = {
  light: {
    background: '$neutral100',
    backgroundHover: '$neutral50',
    backgroundPress: '$neutral200',
    color: '$neutral900',
    colorHover: '$neutral950',
    placeholderColor: '$neutral400',
    borderColor: '$neutral200',
    borderColorHover: '$neutral300',
    shadowColor: 'rgba(0,0,0,0.08)',
  },
}
```

---

## 12. Admin Web — Component Library and Global CSS

**Component library:** shadcn/ui (Radix UI + Tailwind CSS)

The admin web app uses shadcn/ui as its component library. Use shadcn components for all interactive elements: Button, Input, Dialog, Table, Badge, DropdownMenu, Select, Textarea, Card, Separator, Tooltip, and Sheet.

Install components via:

```bash
cd apps/admin
npx shadcn@latest add <component>
```

Installed components live in `apps/admin/src/components/ui/`.

The CSS custom properties below (in `globals.css`) act as the design token bridge: the shadcn theme variables are overridden to match the Annai Illam brand palette defined in Section 1.

### Global CSS Variables

For `apps/admin/src/app/globals.css`:

```css
:root {
  /* Brand */
  --color-brand-900: #0D2E1E;
  --color-brand-800: #113D28;
  --color-brand-700: #165233;
  --color-brand-600: #1A6640;
  --color-brand-400: #25A263;
  --color-brand-300: #4DBF87;
  --color-brand-100: #D4F0E3;
  --color-brand-50:  #EDFAF3;

  /* Text */
  --color-text-primary:    #1C1917;
  --color-text-secondary:  #57534E;
  --color-text-tertiary:   #78716C;
  --color-text-disabled:   #A8A29E;

  /* Surfaces */
  --surface-page:          #F5F5F4;
  --surface-card:          #FFFFFF;
  --surface-subtle:        #FAFAF9;
  --surface-sidebar:       #0D2E1E;
  --surface-overlay:       rgba(0, 0, 0, 0.45);

  /* Borders */
  --border-subtle:         #E7E5E4;
  --border-default:        #D6D3D1;
  --border-strong:         #A8A29E;
  --border-brand:          #1A6640;

  /* Semantic */
  --success:        #22C55E; --success-bg: #DCFCE7; --success-text: #15803D;
  --warning:        #F59E0B; --warning-bg: #FEF3C7; --warning-text: #B45309;
  --danger:         #EF4444; --danger-bg:  #FEE2E2; --danger-text:  #B91C1C;
  --info:           #3B82F6; --info-bg:    #DBEAFE; --info-text:    #1D4ED8;
  --purple:         #8B5CF6; --purple-bg:  #EDE9FE; --purple-text:  #6D28D9;
  --teal:           #06B6D4; --teal-bg:    #CFFAFE; --teal-text:    #0E7490;

  /* Typography */
  --font-display: 'Fraunces', Georgia, serif;
  --font-ui:      'Geist', system-ui, sans-serif;
  --font-mono:    'Geist Mono', ui-monospace, monospace;

  /* Shadows */
  --shadow-xs:    0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:    0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:    0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.04);
  --shadow-xl:    0 20px 25px rgba(0,0,0,0.08), 0 8px 10px rgba(0,0,0,0.04);
  --shadow-brand: 0 4px 14px rgba(26,102,64,0.25);

  /* Radius */
  --radius-sm:    4px;
  --radius-md:    8px;
  --radius-lg:    12px;
  --radius-xl:    16px;
  --radius-2xl:   24px;
  --radius-full:  9999px;

  /* Transitions */
  --transition-fast:   0.12s ease;
  --transition-base:   0.15s ease;
  --transition-slow:   0.25s ease;
  --transition-spring: cubic-bezier(0.16, 1, 0.3, 1);
}

* {
  box-sizing: border-box;
}

body {
  font-family: var(--font-ui);
  background-color: var(--surface-page);
  color: var(--color-text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

---

## 13. Accessibility Standards

```
Colour contrast minimums:
  Body text on white:         7.2:1 (#1C1917) — AAA
  Secondary text on white:    4.6:1 (#57534E) — AA
  Brand button text:          7.2:1 (white on #1A6640) — AAA
  All status badges:          All combinations verified at ≥ 4.5:1

Focus states:
  All interactive elements:   Visible focus ring (2px white + 4px brand)
  Keyboard navigation:        Full support on admin web
  Skip-to-content link:       In admin web layout, visually hidden until focus

Touch targets (mobile):
  All tappable elements:      Minimum 44pt × 44pt
  Primary CTA (check-in):     56px height

Screen reader support:
  Icon-only buttons:          aria-label on every one
  Status badges:              aria-label="Status: In Progress"
  Loading regions:            aria-live="polite"
  Form errors:                role="alert" on error text
  Data tables:                Proper <th scope> attributes
  Images:                     alt text or aria-hidden="true" if decorative
```

---

## 14. Production Design Rules (Non-Negotiable)

```
1.  Every screen has exactly ONE primary action — never two equal-weight CTAs.

2.  Status is shown before detail — badge appears at the top of every record.

3.  Destructive actions are never on the main screen — always inside a
    confirmation modal that spells out the consequence.

4.  Loading states never show blank space — skeleton loaders always, immediately.

5.  Empty states are designed — every empty list has an icon, message, and
    optional action. No accidentally blank screens.

6.  Error messages are human — no stack traces, no HTTP codes, no "undefined"
    shown to users. Write the message as if talking to a non-technical person.

7.  Confirmation modals explain consequences — not just "Are you sure?"
    They say: "Worker [Name] will be notified that their assignment was removed."

8.  Numbers always use mono font — all amounts, counts, times, IDs, dates
    use Geist Mono regardless of surrounding context.

9.  Forms validate on blur, not on submit — show errors field-by-field
    immediately after the user leaves the field, never only on submit.

10. Navigation has no dead ends — every error state, empty state, and
    confirmation screen has a clear next action.

11. Status colours are never used decoratively — green means success/approved,
    red means danger/rejected, amber means pending. Always. No exceptions.

12. Mobile type minimum size is 13px — nothing smaller, ever, on mobile screens.

13. Never use opacity for disabled states alone — also change the cursor
    and remove pointer events. Opacity 0.4 alone still looks clickable.

14. Animations respect prefers-reduced-motion — wrap all animations in
    @media (prefers-reduced-motion: no-preference).
```