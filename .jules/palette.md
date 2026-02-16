## 2025-05-27 - Glassmorphism Focus Visibility
**Learning:** The translucent "glass" style (`background: rgba(...)`) provides insufficient contrast for default browser focus rings, rendering keyboard navigation nearly invisible against the dark space background.
**Action:** Explicitly define `:focus-visible` styles using a high-contrast glow (e.g., `box-shadow: 0 0 15px rgba(68, 221, 255, 0.6)`) and outline (`outline: 2px solid #4df`) for all interactive elements in `glass.css`.

## 2026-02-15 - Async Operation Feedback
**Learning:** Users lack confidence in async operations (like API calculations) without explicit loading states and error feedback. Silent failures (console logs) are particularly problematic.
**Action:** Always implement visible loading indicators (e.g., spinners) and inline error messages for form submissions and data fetching. Ensure inputs have HTML validation attributes (min/max) as a first line of defense.

## 2026-03-01 - Synchronized Input Precision
**Learning:** Sliders are intuitive for exploration but poor for precision. Users often struggle to set exact values (e.g., `0.35`) using only a range input.
**Action:** Always pair range inputs with a synchronized number input (`type="number"`) for scientific or precision-heavy controls. Ensure two-way binding updates both visuals and underlying models immediately.
