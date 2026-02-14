## 2025-05-27 - Glassmorphism Focus Visibility
**Learning:** The translucent "glass" style (`background: rgba(...)`) provides insufficient contrast for default browser focus rings, rendering keyboard navigation nearly invisible against the dark space background.
**Action:** Explicitly define `:focus-visible` styles using a high-contrast glow (e.g., `box-shadow: 0 0 15px rgba(68, 221, 255, 0.6)`) and outline (`outline: 2px solid #4df`) for all interactive elements in `glass.css`.
