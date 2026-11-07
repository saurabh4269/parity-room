---
name: Parity Room
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353943'
  surface-container-lowest: '#0a0e17'
  surface-container-low: '#181b25'
  surface-container: '#1c1f29'
  surface-container-high: '#262a34'
  surface-container-highest: '#31353f'
  on-surface: '#dfe2ef'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#dfe2ef'
  inverse-on-surface: '#2c303a'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#b4c5ff'
  on-secondary: '#002a78'
  secondary-container: '#0053db'
  on-secondary-container: '#cdd7ff'
  tertiary: '#6adbff'
  on-tertiary: '#003543'
  tertiary-container: '#00c1ea'
  on-tertiary-container: '#004b5c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#b6ebff'
  tertiary-fixed-dim: '#47d6ff'
  on-tertiary-fixed: '#001f28'
  on-tertiary-fixed-variant: '#004e60'
  background: '#0f131c'
  on-background: '#dfe2ef'
  surface-variant: '#31353f'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-mobile: 0.75rem
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
  space-2xl: 2rem
---

## Brand & Style

This design system targets Staff-plus engineers, infrastructure architects, and release leads under operational pressure. The environment balances extreme density with absolute sensory calm. The experience minimizes cognitive fatigue during high-stakes triage across staging, canary, and global edge deployments.

The design movement combines **Instrumental Minimalism** with **Technical Precision**:
- **Tactile Optics:** Deep layered voids punctuated by razor-thin slate dividers, evoking an aerospace mission-control console.
- **Calm Observability:** Restrained luminescence. Accent illumination is reserved strictly for interactive vectors, system mutations, and differential state diagnostics.
- **Zero Decorative Noise:** Elimination of heavy drop shadows, rounded friendly geometries, and decorative illustrations in favor of structured data ribbons, explicit boundary lines, and structural alignment.

## Colors

The palette establishes an absolute contrast hierarchy designed for low-light operator focus and WCAG AAA compliance.

### Background & Surface Hierarchy
- `bg-void`: `#090D16` — Global application backdrop, canvas floor.
- `bg-surface-base`: `#0D121F` — Panels, pinned rails, navigation bars.
- `bg-surface-raised`: `#141C2E` — Hover states, modal dialogs, flyouts, floating overlays.
- `bg-surface-active`: `#1E293B` — Selected rows, active tabs, active diff segments.

### Boundaries & Structural Grid
- `border-subtle`: `#1E293B` — Standard structural bounding boxes, panel borders, row separators.
- `border-strong`: `#334155` — Active panel focus, hover borders, interactive component outlines.
- `border-accent`: `rgba(56, 189, 248, 0.4)` — Active focus rings and target nodes.

### Telemetry & Action Accents
- `primary`: `#38BDF8` — Primary focus, active toggle states, current execution pointer.
- `secondary`: `#2563EB` — Foundational anchors, resting interactive controls, structural badges.
- `tertiary`: `#00D2FF` — High-intensity highlights, real-time live telemetry beacons.

### Semantic Verification Status (Color-Blind Accessible)
- **Passing / Parity Verified:** `#10B981` (Border/Icon: `#059669`, Fill: `rgba(16, 185, 129, 0.08)`).
- **Failing / Discrepancy Detected:** `#F43F5E` (Border/Icon: `#EF4444`, Fill: `rgba(244, 63, 94, 0.08)`).
- **In-Progress / Divergent Staging:** `#F59E0B` (Border/Icon: `#D97706`, Fill: `rgba(245, 158, 11, 0.08)`).
- **Muted / Inactive / Skipped:** `#64748B` (Border/Icon: `#475569`, Fill: `rgba(100, 116, 139, 0.08)`).

## Typography

The type system implements a strict functional dichotomy: **Inter** structures structural layout and contextual reading, while **JetBrains Mono** surfaces all telemetry, system identities, Git hashes, diff counts, and runtime state.

### Rules for Application
- **Inter** is constrained to section headers, meta descriptions, operational actions, and documentation popovers. It utilizes neutral gray rendering (`#E2E8F0` on `#090D16`) to eliminate terminal eye strain.
- **JetBrains Mono** governs system metadata: SHA-1 tags, latency metrics (`42ms`), environment matrices (`us-east-1a`), and memory footprints. Numeric data must utilize tabular lining (`font-variant-numeric: tabular-nums`).
- **All-Caps Micro-Labels:** UI labels (`label-sm`) use uppercase JetBrains Mono with expanded letter-spacing (`0.06em`) to denote environment scopes (e.g., `PROD-CANARY`, `STAGING-04`).

## Layout & Spacing

The architecture operates on a baseline **4px grid** unified through a multi-tier technical cockpit layout.

### Layout Model
- **Grid Execution:** 24-column fluid workbench grid with fixed outer gutters. Columns split dynamically: 6-column matrix comparison views, 12-column side-by-side terminal differential views, or 24-column consolidated trace logs.
- **Micro-Gaps:** Structural telemetry blocks snap tightly using `space-xs` (4px) and `space-sm` (8px) to retain continuous optical paths across disparate environment rows.

### Breakpoints & Adaptive Reflow
- **Desktop Ultrawide (>1920px):** 4-pane simultaneous parity comparison (Dev, Staging, Canary, Production) locked side-by-side. Outer margins: `space-xl`.
- **Desktop Standard (1280px - 1919px):** 2-pane comparison with collapsible environment selector drawer. Canvas gutter: `gutter` (16px).
- **Tablet / Laptop Compact (768px - 1279px):** Stacked differential views with sticky comparative metric headers. Gutter drops to `gutter-compact` (8px).
- **Mobile (<768px):** Single-column diagnostic feed. Multi-target matrix collapses into segmented swipe tabs. Canvas margin: `margin-mobile` (12px).

## Elevation & Depth

This design system rejects physical elevation and simulated gravity. In place of cast drop shadows, depth is achieved exclusively through **Surface Tiers** and **Low-Contrast Technical Outlines**.

### Elevation Tiers
- **Tier 0 (Base Void):** `#090D16`. The canvas foundation.
- **Tier 1 (Structural Panels):** `#0D121F` with a continuous 1px outline of `#1E293B`. Used for execution tracks, environment panels, and terminal outputs.
- **Tier 2 (Interactive Context & Headers):** `#141C2E` with 1px border of `#334155`. Used for active comparison cards, filter banks, and sticky table heads.
- **Tier 3 (Floating Overlays & Inspections):** `#141C2E` framed with a dual border: 1px inner border of `#38BDF8` at 30% opacity, surrounded by an outer 1px structural line of `#1E293B`. A concentrated, neutral ambient glow (`0 0 24px rgba(0, 0, 0, 0.6)`) provides z-index separation over running code.

### Differential Highlights
Divergent code states generate localized, zero-blur backdrops:
- Match: Inset boundary `1px solid rgba(16, 185, 129, 0.2)`.
- Conflict: Inset boundary `1px solid rgba(244, 63, 94, 0.4)` with an inline background tint of `rgba(244, 63, 94, 0.04)`.

## Shapes

The shape system leverages **Soft Architecture (Level 1)**: crisp, engineering-grade contours that maintain structural rigidity without harsh visual artifacts.

### Radii Allocation
- **Atomic Data Points (Badges, Status Nodes, Counters):** `2px` border radius (`rounded-xs`). Maintains monospaced character bounds without clipping.
- **Inputs, Buttons, and Data Cells:** `4px` border radius (`space-xs`). Crisp tactile definition.
- **Panels, Windows, and Comparison Columns:** `6px` border radius (`rounded-sm`). Subtle rounding that preserves maximum square millimeter viewing area for long log strings.
- **Pill Exceptions:** Restricted solely to alive/dead connection indicator pips (concentric circles, `border-radius: 9999px`).

## Components

### Buttons
- **Primary Execution (Action):** Solid background of `#2563EB`, text `#FFFFFF`, border `1px solid #38BDF8`. Hover shifts to `#38BDF8` with text `#090D16`. Focus outline: 2px offset ring `rgba(56, 189, 248, 0.4)`.
- **Secondary (Inspect / Compare):** Background `#141C2E`, text `#E2E8F0`, border `1px solid #1E293B`. Hover state shifts border to `#334155` and text to `#38BDF8`.
- **Destructive (Halt / Abort Rollout):** Background `rgba(239, 68, 68, 0.1)`, text `#F43F5E`, border `1px solid rgba(239, 68, 68, 0.4)`.

### Status Badges & Chips
- **Geometry:** Height 20px, horizontal padding 6px, border-radius 2px. Label uses `label-sm` (uppercase monospaced).
- **Passing Badge:** Background `rgba(16, 185, 129, 0.1)`, text `#10B981`, border `1px solid rgba(16, 185, 129, 0.3)`. Prefixed with a non-color geometric icon (`✓`).
- **Failing Badge:** Background `rgba(244, 63, 94, 0.1)`, text `#F43F5E`, border `1px solid rgba(244, 63, 94, 0.3)`. Prefixed with a non-color geometric icon (`✕`).
- **Running Badge:** Background `rgba(245, 158, 11, 0.1)`, text `#F59E0B`, border `1px solid rgba(245, 158, 11, 0.3)`. Prefixed with an animated pulse dot or glyph (`◌`).

### Data Comparison Grid & Lists
- **Rows:** Minimum height 32px. Alternating zebra row striping avoided; segmentation achieved via 1px horizontal borders (`#1E293B`).
- **Hover Row:** Background shifts instantly to `#141C2E` with a leading 2px vertical border accent in `#38BDF8`.
- **Diff Display:** Side-by-side split cells. Deletions highlighted in `rgba(244, 63, 94, 0.15)` with strikethrough; additions highlighted in `rgba(16, 185, 129, 0.15)`.

### Form Controls (Inputs, Checkboxes & Radios)
- **Text / Search Inputs:** Background `#0D121F`, border `1px solid #1E293B`, font `code-md`, text `#F8FAFC`. Placeholder `#475569`. Active focus: border `#38BDF8`, inner ambient inset line.
- **Checkboxes & Radios:** 14px square/circle, background `#090D16`, border `1px solid #334155`. Checked state fills `#2563EB` with `#FFFFFF` glyph. Indeterminate states display a centered monospaced minus `-`.

### Diagnostic Panels & Cards
- **Shell:** Background `#0D121F`, border `1px solid #1E293B`, roundedness 4px.
- **Panel Header:** Height 36px, background `#090D16`, bottom border `1px solid #1E293B`, padding 0 12px. Contains environment descriptor chip, runtime health status, and localized action buttons.

### Specialized Component: Parity Split Matrix
- Dual/Quad container spanning heterogeneous staging targets.
- Features a synchronized vertical scroll-lock toggle and an anchored diff navigator strip displaying high-density block indicators of passing/failing assertions along the right rail.