---
name: Pravaah Technical Core
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#ddb7ff'
  on-secondary: '#490080'
  secondary-container: '#6f00be'
  on-secondary-container: '#d6a9ff'
  tertiary: '#4cd7f6'
  on-tertiary: '#003640'
  tertiary-container: '#009eb9'
  on-tertiary-container: '#002f38'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#f0dbff'
  secondary-fixed-dim: '#ddb7ff'
  on-secondary-fixed: '#2c0051'
  on-secondary-fixed-variant: '#6900b3'
  tertiary-fixed: '#acedff'
  tertiary-fixed-dim: '#4cd7f6'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5c'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
typography:
  display:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  gutter: 16px
  margin_desktop: 32px
  margin_mobile: 16px
---

## Brand & Style
The design system for Pravaah is engineered for an AI-native backend environment where "everything flows." The brand personality is deeply technical, precise, and futuristic, aimed at developers who demand high-performance tools. 

The aesthetic sits at the intersection of **Minimalism** and **Glassmorphism**, drawing heavy influence from high-end developer platforms. It utilizes a dark-first approach to reduce eye strain during deep-work sessions. The UI is characterized by thin, high-precision lines, subtle back-lit glows that signify "AI intelligence," and a structured, rhythmic layout that mimics the logic of efficient code. Every element should feel fast, responsive, and ethereal yet grounded in engineering rigor.

## Colors
The palette is centered on "Deep Obsidian" surfaces to provide a high-contrast canvas for technical data. 

- **Primary & Tertiary:** Electric Blue and Cyan are used for standard actions, flow indicators, and connectivity status.
- **AI Glow:** Purple is reserved exclusively for AI-driven features, suggestions, and automated event logic.
- **Semantic States:** Success and Warning colors use high-saturation tokens but are often paired with a 10% opacity background tint for status chips.
- **Borders:** Instead of solid grays, borders use a semi-transparent white/blue mix to create a "glassmorphic" edge that feels lighter than the dark background.

## Typography
The typography system prioritizes legibility in dense data environments. **Geist** provides a clean, modern sans-serif feel for the interface, while **JetBrains Mono** is utilized for all technical outputs, labels, and code blocks.

For mobile, `headline-lg` should scale down to 24px. Use `label-caps` for table headers and small metadata tags to maintain a disciplined, technical look. Tracking (letter-spacing) should be tightened for headlines and opened slightly for monospaced labels to ensure maximum clarity at small sizes.

## Layout & Spacing
This design system follows a strict **8px grid** to ensure mathematical harmony. 

- **Grid:** Use a 12-column fluid grid for the main content area with 16px gutters.
- **Sidebar:** A fixed 240px navigation sidebar on desktop, collapsing to a 64px icon rail or drawer on mobile.
- **Flow Containers:** Event visualizers and node-based editors should use an infinite-canvas feel with a dotted background grid visible at 24px intervals.
- **Responsiveness:** On mobile, margins reduce to 16px, and modular cards stack vertically. Navigation transitions to a bottom bar or a condensed top-level menu.

## Elevation & Depth
Depth is achieved through **Tonal Layers** and **Glassmorphism** rather than traditional heavy shadows.

- **Surface Levels:** The base level is `#0B0F19`. Cards and modals sit on `#111827`.
- **Backdrop Blur:** All overlays (modals, dropdowns, sidebars) must implement `backdrop-blur-md` (approx 12px-16px) with a subtle `rgba(255, 255, 255, 0.03)` fill.
- **Glows:** Active states use a soft outer glow (`box-shadow`) matching the accent color (e.g., a 15px blurred Cyan glow for a selected node).
- **Outlines:** Use 1px borders for all containers. These borders should have a linear gradient from top-left to bottom-right, transitioning from a slightly lighter gray to the deep background color.

## Shapes
The shape language is "Soft-Tech." It avoids the roundness of consumer apps in favor of a more professional, "machined" look.

- **Standard Radius:** 0.25rem (4px) for input fields, small buttons, and tags.
- **Container Radius:** 0.5rem (8px) for cards, modals, and larger sections.
- **Connectors:** Flow lines between nodes should be 1.5px thick with a 2px radius on corners to maintain the technical aesthetic.
- **Indicators:** Health status dots and activity pulses should be perfect circles.

## Components
- **Buttons:** Primary buttons use a solid Electric Blue fill. Secondary buttons are ghost-style with a subtle border and a low-opacity hover state.
- **Modular Cards:** Plugin management cards feature a top-border accent (1px) indicating the category (AI, Database, etc.) and use "Deep Obsidian" backgrounds.
- **Sidebar:** Navigation items include a 2px vertical "indicator glow" on the left side when active.
- **Node Visualizers:** Boxes with monospaced text, connected by thin, directional gradient lines that pulse to indicate data flow.
- **Code Snippets:** Syntax highlighting should use a custom theme based on the accent palette (Cyan for strings, Purple for functions, Emerald for comments).
- **Health Indicators:** A small circle icon with a multi-layered CSS animation—a solid core with a secondary, expanding ring at 30% opacity to simulate a "heartbeat" or "pulse."
- **Input Fields:** Dark fill (`#0B0F19`) with a 1px border that glows Primary Blue on focus. Use monospaced font for placeholder text in technical settings.