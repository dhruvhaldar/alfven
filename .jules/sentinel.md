## 2025-02-28 - Prevent DOM-based XSS with textContent
**Vulnerability:** A potential DOM-based Cross-Site Scripting (XSS) vulnerability was found in `public/js/ui.js` where user-driven error messages were rendered into the DOM using `errorDiv.innerHTML = \`⚠️ ${msg}\`;`.
**Learning:** Even though the frontend controlled the `msg` content in this specific scenario, directly interpolating dynamic strings into `innerHTML` is an unsafe pattern that can easily be exploited if the input source becomes untrusted or dynamic in the future.
**Prevention:** Always use `textContent` (or `innerText`) instead of `innerHTML` when rendering user input or dynamic messages that do not specifically require HTML execution, as it safely encodes the text.
