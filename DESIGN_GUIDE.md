# CDAI Lite – Design Guide

## 🎯 Core Philosophy
CDAI Lite is a decision-first AI tool focused on helping users quickly compare and select the best outputs.

Key goals:
- Fast comparison
- Clear selection
- Minimal cognitive load

Avoid clutter, hidden UI, and unnecessary actions.

---

## 🧠 UX Principles
1. Prioritize decision-making over feature exposure
2. Make primary actions visually dominant
3. Ensure all state changes are obvious
4. Avoid hidden interactions
5. Perceived speed is critical

---

## 🎨 Design System

### Colors
- Use gradients, not flat colors
- --grad-main → primary actions
- --grad-soft → backgrounds

### Background
- App: #f6f7fb
- Cards: white
- Inputs: #f1f3f7

---

## 🔤 Typography
- Font: Inter
- 400 → normal
- 500 → emphasis
- 600 → headings

---

## 🧱 Layout
- Left: control panel (sticky)
- Right: results grid
- Do not alter layout structure

---

## 🧾 Result Cards

Each card = decision unit

### Structure
- Floating checkmark (top-left)
- Top meta (Prompt, Model)
- Image
- Hover overlay (Preview, Select)
- Bottom meta (LoRA)

### Behavior
- Click anywhere → select
- Selected state:
  - Glow
  - Checkmark visible
  - Button changes to "Selected ✓"

### Overlay
- Only 2 actions:
  - Preview (secondary)
  - Select (primary)
- Select must be visually dominant

---

## 🧠 Prompt System
- Multiple prompts supported
- Auto labels: Prompt A, B, C...
- Add/remove dynamically

---

## 🏷️ Tags (Models / LoRA)
- Use pill-style selectable tags
- Active state:
  - Gradient background
  - Glow
  - Checkmark

---

## ⚡ Batch Behavior
- Before: "Ready to generate"
- During: shimmer loading
- After: enable actions

---

## 🎯 Interaction Rules
- Card click = select
- Select button = same action
- Preview = open modal (future)

---

## ✨ Micro Interactions
- Hover lift
- Glow on selection
- Shimmer loading
- Button scale on hover

---

## 🚫 Avoid
- Dropdowns for multi-select
- Too many buttons
- Hidden interactions
- Flat colors

---

## 🧠 Visual Hierarchy
1. Image
2. Select action
3. Metadata
4. Preview

---

## 🚀 Future
- Group by prompt
- Compare mode
- Preview modal
