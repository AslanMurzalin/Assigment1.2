# Design System & UI Guidelines: Link Saver (v1)

This document establishes the official visual identity, color palette, typography, and component styling rules for the **Link Saver** application. Every agent and engineer working on the frontend must adhere to these design specifications.

---

## 1. Visual Identity & Theme Philosophy

- **Aesthetic**: Warm, crisp, editorial, and minimalist (inspired by modern developer tools like Substack, Linear, and Claude).
- **Core Theme**: **Orange & White** palette.
  - High-contrast readability.
  - Clean white card surfaces elevated against subtle warm canvas backgrounds.
  - Energetic orange accents for primary interactive elements, active states, and branding.

---

## 2. Color Palette & Token Definitions

### 2.1 Primary & Accent Colors (Orange)
| Token / Tailwind Class | Hex Value | Usage |
|---|---|---|
| `orange-50` | `#fff7ed` | Subtle badge backgrounds, tag chips, input focus highlights |
| `orange-100` | `#ffedd5` | Hovered tag chips, border accents, alert backgrounds |
| `orange-200` | `#fed7aa` | Active borders, badge outlines |
| `orange-500` | `#f97316` | Bright accent, focus outlines, animated indicators |
| `orange-600` | `#ea580c` | **Primary Brand Color**: Primary buttons, key logos, active links |
| `orange-700` | `#c2410c` | Button hover states, emphasized text links |
| `orange-800` | `#9a3412` | Dark active states |

### 2.2 Neutrals & Surfaces (Warm White & Stone)
| Token / Tailwind Class | Hex Value | Usage |
|---|---|---|
| `white` | `#ffffff` | Primary card surfaces, modal sheets, dropdown menus |
| `stone-50` / `orange-50/20` | `#fafaf9` | Page body background (canvas) |
| `stone-100` | `#f5f5f4` | Secondary button backgrounds, disabled controls |
| `stone-200` | `#e7e5e4` | Standard card and input borders |
| `stone-400` | `#a8a29e` | Placeholder text, inactive icons |
| `stone-500` | `#78716c` | Secondary labels, timestamps, subtitle text |
| `stone-700` | `#44403c` | Form labels, card body text, secondary headings |
| `stone-900` | `#1c1917` | Primary headings, titles, high-emphasis text |

### 2.3 Semantic Accents
| Semantic Role | Classes | Usage |
|---|---|---|
| **YouTube Media** | `bg-red-50 text-red-700 border-red-200` / `bg-red-600 hover:bg-red-700` | YouTube site badge & 720p stream download button |
| **Success** | `bg-emerald-50 text-emerald-700 border-emerald-200` / `bg-emerald-600` | Download confirmed, success notifications |
| **Danger / Destructive** | `bg-rose-50 text-rose-700 border-rose-200` / `hover:text-rose-600` | Delete link button, validation error messages |

---

## 3. Typography & Spacing

- **Font Family**: Modern system sans-serif (`system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`).
- **Hierarchy**:
  - `text-3xl font-extrabold text-stone-900 tracking-tight`: Main page titles, Auth brand headers.
  - `text-lg font-bold text-stone-900`: Navigation brand title, modal headings.
  - `text-base font-semibold text-stone-900`: Link card titles, section headings.
  - `text-sm font-medium text-stone-700`: Form labels, button text, search input.
  - `text-xs text-stone-500`: Metadata, timestamps, helper descriptions, tag chips.
  - `text-[11px]`: Compact badge labels and URL domains.

---

## 4. Component Design Patterns

### 4.1 Buttons
- **Primary Button**:
  ```tsx
  className="py-2.5 px-5 bg-orange-600 hover:bg-orange-700 text-white font-medium text-sm rounded-xl shadow-xs hover:shadow transition disabled:opacity-50 flex items-center justify-center gap-2"
  ```
- **Secondary / Ghost Button**:
  ```tsx
  className="py-2 px-3.5 bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-medium rounded-xl transition"
  ```
- **YouTube Download Button**:
  ```tsx
  className="w-full py-2 px-3 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white shadow-xs transition"
  ```

### 4.2 Inputs & Form Controls
- **Text & Search Inputs**:
  ```tsx
  className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 bg-white transition placeholder:text-stone-400"
  ```
- **Textareas**:
  ```tsx
  className="w-full px-3.5 py-2 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 bg-white transition resize-y"
  ```

### 4.3 Tags & Chips
- **Interactive Tag Chip**:
  ```tsx
  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200"
  ```
- **Filter Tag Pill (Active)**:
  ```tsx
  className="bg-orange-600 text-white shadow-xs"
  ```
- **Filter Tag Pill (Inactive)**:
  ```tsx
  className="bg-white hover:bg-orange-50 text-stone-600 hover:text-orange-700 border border-stone-200"
  ```

### 4.4 Cards & Surfaces
- **Card Container**:
  ```tsx
  className="bg-white rounded-2xl border border-stone-200/90 hover:border-stone-300 p-5 shadow-xs hover:shadow-md transition-all duration-200"
  ```
- **Modal Dialog Sheet**:
  ```tsx
  className="w-full max-w-lg bg-white rounded-2xl shadow-xl border border-stone-200 overflow-hidden"
  ```

---

## 5. Responsive Design Rules

- **Mobile (<640px)**: 1 column grid, full-width buttons, compact header with email abbreviation if needed.
- **Tablet (640px - 1024px)**: 2 column grid for link cards.
- **Desktop (>1024px)**: 3 column grid for link cards, max-width `max-w-6xl` centered.
