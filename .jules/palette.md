## 2025-05-27 - Glassmorphism Focus Visibility
**Learning:** The translucent "glass" style (`background: rgba(...)`) provides insufficient contrast for default browser focus rings, rendering keyboard navigation nearly invisible against the dark space background.
**Action:** Explicitly define `:focus-visible` styles using a high-contrast glow (e.g., `box-shadow: 0 0 15px rgba(68, 221, 255, 0.6)`) and outline (`outline: 2px solid #4df`) for all interactive elements in `glass.css`.

## 2026-02-15 - Async Operation Feedback
**Learning:** Users lack confidence in async operations (like API calculations) without explicit loading states and error feedback. Silent failures (console logs) are particularly problematic.
**Action:** Always implement visible loading indicators (e.g., spinners) and inline error messages for form submissions and data fetching. Ensure inputs have HTML validation attributes (min/max) as a first line of defense.

## 2026-03-01 - Synchronized Input Precision
**Learning:** Sliders are intuitive for exploration but poor for precision. Users often struggle to set exact values (e.g., `0.35`) using only a range input.
**Action:** Always pair range inputs with a synchronized number input (`type="number"`) for scientific or precision-heavy controls. Ensure two-way binding updates both visuals and underlying models immediately.

## 2026-05-27 - Loading Spinner Pattern
**Learning:** Async operations like Magnetosphere Standoff calculation need immediate visual feedback to prevent user uncertainty.
**Action:** Use the global `.loading-spinner` class and `aria-busy="true"` on the output container immediately upon user interaction, before the debounced request fires.

## 2026-05-28 - Canvas Accessibility
**Learning:** Canvas elements used for data visualization (like charts) are completely invisible to screen readers without explicit roles and labels.
**Action:** Always add `role="img"` and a descriptive `aria-label` to `<canvas>` elements. For complex charts, provide a summary or data table if possible.

## 2026-05-29 - Inline Validation Feedback
**Learning:** Generic error messages ("Positive values required") without visual cues cause frustration as users must guess which input is invalid.
**Action:** Implement `validateInput` helper to apply `.invalid` class and `aria-invalid="true"` to specific fields, and auto-clear these states on user input.

## 2026-06-01 - Keyboard Shortcuts for Calculator Inputs
**Learning:** In "calculator-style" interfaces where users input multiple numerical values, they instinctively press "Enter" to trigger the calculation. Forcing them to tab to or click a "Calculate" button breaks their flow.
**Action:** Always attach a `keydown` listener to input fields that triggers the primary action button when "Enter" is pressed, especially if the inputs are not wrapped in a formal `<form>`.

## 2026-06-03 - Result Interaction Delight
**Learning:** In educational/scientific tools, users frequently need to extract precise calculation results for use elsewhere (e.g., reports). Static text requires manual selection which is error-prone.
**Action:** Implement "Click to Copy" functionality on result displays using the Clipboard API, providing immediate visual (class change) and accessible (title update) feedback.

## 2026-02-28 - Dynamic Error Announcement
**Learning:** Dynamically generated error messages injected into the DOM (e.g., failed form submissions or calculations) are not automatically announced by screen readers, leaving visually impaired users unaware of failures.
**Action:** Always add `role="alert"` to dynamically created error message containers to ensure assertive announcement by assistive technologies.

## 2026-03-02 - Button Disabled State
**Learning:** While buttons were programmatically disabled during async operations, the lack of an explicit `:disabled` CSS state meant they still looked clickable, confusing users.
**Action:** Add explicit `.glass-button:disabled` styles (e.g., reduced opacity, `cursor: not-allowed`) to visually distinguish the disabled state from the active and hover states.

## 2026-03-03 - Accessible Button-Result Relationships
**Learning:** Screen reader users can struggle to understand which part of the page will update when clicking a generic "Calculate" button if the results container is separate from the button.
**Action:** Always use `aria-controls="[id-of-results-container]"` on action buttons that trigger calculations or fetch data to explicitly link the trigger to the dynamic output region.

## 2026-07-25 - Form Validation Focus Guidance
**Learning:** When form validation fails after clicking a button, simply displaying an error message leaves the user's focus on the button. Screen reader users must manually navigate back up to find the invalid field, which is tedious and confusing.
**Action:** Always programmatically call `.focus()` on the first invalid input when client-side validation fails. This immediately directs both sighted and assistive technology users to the exact location requiring correction. Additionally, visually mark explicitly required fields with a distinctive indicator (like a red asterisk) in the label.
## 2026-08-01 - Document Structure and Semantic HTML
**Learning:** Using `<div>` elements exclusively for document structure and component titles creates a flat document outline. Screen reader users rely on semantic landmarks (`<main>`, `<header>`, `<section>`) and correct heading levels (`<h2>`, `<h3>`) to navigate efficiently. Furthermore, misusing `<label>` tags for read-only values instead of form inputs triggers accessibility validation errors.
**Action:** Always use semantic HTML5 sectioning elements (`<main>`, `<section>`) and properly nested headings (`<h2>` etc.). Link sections to their headings using `aria-labelledby`. Use `<span class="result-label">` or similar instead of `<label>` when displaying read-only data outputs not associated with a form input.

## 2026-08-05 - Transient Visual Feedback Accessibility
**Learning:** Purely visual transient interactions, like displaying a "Copied" icon or changing a color temporarily, are entirely invisible to screen reader users unless accompanied by programmatic announcements.
**Action:** Pair all transient visual feedback interactions with an assertive or polite announcement via an `aria-live` region to ensure parity of experience. Use a global `#sr-announcer` element for this purpose to avoid complex markup additions across components.

## 2026-08-06 - Contextual Context for Interactive Elements
**Learning:** Screen readers announce interactive values (like "10.5 m" or "- K") without the necessary context, leaving visually impaired users guessing what the value represents if they focus directly on a copyable result button.
**Action:** Always assign an `id` to the read-only descriptive text (e.g., `<span class="result-label" id="label-debye">`) and link it to the interactive element using `aria-labelledby="[label-id] [button-id]"`.

## 2026-08-06 - Toggle Switch Accessibility
**Learning:** A standard `<input type="checkbox">` styled as a toggle switch is announced simply as a checkbox. This does not convey the binary switch paradigm to screen reader users, who may not understand its immediate effect.
**Action:** Add `role="switch"` to toggle switches and link them to their dynamic status text (e.g., "Day Mode") using `aria-describedby` so the user is aware of the current state immediately.

## 2026-08-07 - Contextual Error Association
**Learning:** Relying solely on a global error banner (e.g., "Positive values required") when a form contains multiple inputs forces screen reader users to guess which specific field failed validation. Furthermore, retaining a stale global error message while the user is actively correcting the input creates a confusing, conflicting state.
**Action:** Dynamically inject `.inline-error` messages directly adjacent to the offending input and associate them programmatically using `aria-errormessage`. Additionally, ensure that typing in *any* input field clears both the inline error for that field *and* any global error banner associated with the parent container.

## 2026-08-08 - Native Decimal Validation
**Learning:** Default `<input type="number">` elements implicitly use `step="1"`, which blocks decimal input via native browser validation. For scientific parameters, this causes confusing browser-level validation errors when users input valid decimal values.
**Action:** Always add `step="any"` to numeric inputs that represent scientific or continuous variables to ensure native browser validation correctly accepts decimal values.

## 2026-03-13 - Preventing Stale Data Copies in Manual Forms
**Learning:** Users can easily copy outdated results from manual calculation forms (like Plasma Parameters and Aurora Power) if they change inputs but forget to click "Calculate". The interactive copyable results (`.copyable-result`) remain active even when inputs are dirty, leading to potential data errors in their work.
**Action:** Implemented a "stale state" pattern using `.stale-results` (opacity reduction on results) and `.needs-update` (pulsating animation on the calculate button). These are triggered on any input change and cleared upon recalculation, providing clear visual cues that the displayed results no longer match the current inputs. Ensure manual forms always visually distinguish out-of-sync states.

## 2026-03-14 - Smooth Continuous Range Sliders
**Learning:** Default `<input type="range">` elements implicitly use `step="1"`, causing a choppy "snapping" effect when dragged. This feels particularly unpolished and rigid for controls representing continuous scientific parameters (like solar wind density).
**Action:** Always add `step="any"` to both the `<input type="range">` and its synchronized `<input type="number">` pair when representing continuous variables. This provides a fluid, premium dragging experience and ensures native browser validation accepts decimal inputs without errors.

## 2026-08-09 - Client-Side Constraint Sync
**Learning:** Form inputs lacked `max` constraints corresponding to the backend API's Pydantic bounds (e.g., `le=1e30`). Users entering extremely large numbers received generic, global "Calculation failed" API errors instead of immediate, specific inline feedback.
**Action:** Always sync backend bounds (like `min` and `max`) to frontend HTML validation attributes, and enhance the `validateInput` helper to provide specific inline error messages for `rangeOverflow` conditions to prevent frustrating network round-trips for invalid data.

## 2026-08-10 - Screen Reader Invalid State Sync
**Learning:** Adding an `.invalid` CSS class provides a visual indication of validation failure for sighted users, but completely bypasses screen reader users who depend on the `aria-invalid` attribute. If they are not synchronized, a form control may appear invalid visually while reporting as valid contextually.
**Action:** Whenever dynamically adding or removing a CSS class for an invalid state (e.g., `.invalid`), ensure that the corresponding `aria-invalid="true"` or `aria-invalid="false"` attribute is set synchronously on the input element.

## 2026-08-11 - Skip to Content Links
**Learning:** Keyboard-only users and screen reader users must navigate through decorative or repetitive header elements (like the animated background canvas and hero section) before reaching interactive panels.
**Action:** Always include a "Skip to main content" link at the very beginning of the document flow that becomes visible on focus, allowing users to bypass non-interactive elements efficiently.

## 2026-08-12 - Copyable Result Discoverability
**Learning:** Hiding interaction affordances (like clipboard icons) entirely behind hover states is an accessibility and UX anti-pattern. It makes the feature undiscoverable for users on touch devices and forces desktop users to "hunt" for interactivity by randomly hovering.
**Action:** Ensure interactive elements that don't look like standard buttons (like copyable result text) always display a baseline visual affordance, such as a subtle background, border, and a persistently visible (though perhaps lower opacity) icon, to clearly signal their interactivity.

## 2026-08-13 - Tactile Feedback and Cross-Browser Sliders
**Learning:** Default interactive elements (like buttons and copyable results) often feel static when clicked. Sliders use a generic `pointer` cursor, miscommunicating the drag interaction. Furthermore, custom styling for `-webkit-slider-thumb` leaves Firefox users with broken UI.
**Action:** Enhance tactile feedback by applying `transform: scale(0.98)` to buttons/results on `:active`, and scale up slider thumbs on `:hover` and `:active`. Always use `cursor: grab` and `cursor: grabbing` for sliders to communicate the interaction model. Remember to implement `-moz-range-thumb` and `-moz-range-track` pseudo-elements for cross-browser visual consistency.

## 2026-08-14 - Placeholder Guidance in Forms
**Learning:** Users who clear numeric inputs (e.g., in Plasma Parameters or Aurora Power) lose the context of the expected format (like scientific notation `1e6`). A blank input without a placeholder requires them to guess or refer to documentation.
**Action:** Always provide `placeholder` attributes (e.g., "e.g. 1e6") on numeric inputs that require specific formats or typical magnitudes, and style them consistently (e.g., `.glass-input::placeholder`) to maintain design cohesion while offering continuous guidance.

## 2026-08-15 - ARIA Label Overrides and Scientific Units
**Learning:** Using `aria-label` on form inputs completely overrides their native accessible name derived from the `<label>` element. In scientific applications, if critical context (like units such as `cm⁻³` or `km/s`) exists only in the visible label, screen reader users will lose this context if the `aria-label` does not duplicate it.
**Action:** When an explicit visible `<label>` provides complete context (including units), avoid using `aria-label` on the associated input. For synchronized inputs (like a range slider and a number input sharing one label), assign an `id` to the `<label>` and use `aria-labelledby="[label-id]"` on both inputs to ensure the exact visible text, including units, is announced consistently.

## 2026-08-16 - Toggle Interactive Text Affordance
**Learning:** Text labels adjacent to toggle switches (like "Day Mode" / "Night Mode") are often expected to be clickable by users. If implemented as standard `<span>` elements, they fail to act as click targets for the toggle and lack interactive visual affordances, causing minor friction.
**Action:** Always implement text describing a toggle switch's state or function as a `<label for="[toggle-id]">`. Furthermore, add global CSS styles targeting `label[for]` to explicitly provide `cursor: pointer` and subtle hover effects (like text-shadow and color transitions) to visually signal interactivity to sighted users.
