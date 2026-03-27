// Form Validation Helper
function validateInput(input) {
    const val = parseFloat(input.value);
    const maxAttr = input.getAttribute('max');
    const max = maxAttr ? parseFloat(maxAttr) : Infinity;
    const errorId = `${input.id}-error`;
    let errorEl = document.getElementById(errorId);

    if (isNaN(val) || val <= 0 || val > max) {
        input.classList.add('invalid');
        input.setAttribute('aria-invalid', 'true');

        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.id = errorId;
            errorEl.className = 'inline-error';
            errorEl.setAttribute('role', 'alert');
            input.parentNode.appendChild(errorEl);
        }

        if (isNaN(val) || val <= 0) {
            errorEl.textContent = '⚠️ Please enter a positive number.';
        } else if (val > max) {
            const maxStr = max > 10000 ? max.toExponential() : max;
            errorEl.textContent = `⚠️ Value must be \u2264 ${maxStr}.`;
        }

        input.setAttribute('aria-errormessage', errorId);
        return false;
    }

    input.classList.remove('invalid');
    input.setAttribute('aria-invalid', 'false');
    input.removeAttribute('aria-errormessage');
    if (errorEl) {
        errorEl.remove();
    }
    return true;
}

function clearErrorState(e) {
     const input = e.target;
     input.classList.remove('invalid');
     input.setAttribute('aria-invalid', 'false');
     input.removeAttribute('aria-errormessage');

     const errorId = `${input.id}-error`;
     const errorEl = document.getElementById(errorId);
     if (errorEl) {
         errorEl.remove();
     }

     // Also clear any global error message in the container
     const container = input.closest('.glass-panel');
     if (container) {
         const globalError = container.querySelector('.error-message');
         if (globalError) {
             globalError.remove();
         }
     }
}

function setLoading(btn, container, isLoading) {
    if (!btn) return;
    if (isLoading) {
         btn.dataset.text = btn.innerText;

         // 🛡️ Sentinel: Prevent XSS by using textContent and createElement instead of innerHTML
         btn.textContent = ' Calculating...';
         const spinner = document.createElement('span');
         spinner.className = 'loading-spinner';
         spinner.setAttribute('aria-hidden', 'true');
         btn.prepend(spinner);

         btn.disabled = true;
         btn.style.cursor = "wait";
         container.setAttribute('aria-busy', 'true');

         // Remove stale states when calculation starts
         btn.classList.remove('needs-update');
         container.classList.remove('stale-results');

         const error = container.querySelector('.error-message');
         if(error) error.remove();
    } else {
         btn.innerText = btn.dataset.text || "Calculate";
         btn.disabled = false;
         btn.style.cursor = "pointer";
         container.setAttribute('aria-busy', 'false');
    }
}

function showError(container, msg) {
     const existingError = container.querySelector('.error-message');
     if (existingError) {
          existingError.remove();
     }
     const errorDiv = document.createElement('div');
     errorDiv.className = 'error-message';
     errorDiv.style.color = '#ff6b6b';
     errorDiv.style.marginTop = '10px';
     errorDiv.style.fontSize = '0.9rem';
     errorDiv.setAttribute('role', 'alert');
     // 🛡️ Sentinel: Prevent XSS by using textContent instead of innerHTML
     errorDiv.textContent = `⚠️ ${msg}`;
     container.appendChild(errorDiv);
}

// Plasma Calculation
async function calcPlasma(btn) {
    const resultsContainer = document.getElementById('plasma-results');
    const nInput = document.getElementById('plasma-n');
    const TInput = document.getElementById('plasma-T');

    const nValid = validateInput(nInput);
    const TValid = validateInput(TInput);

    if (!nValid || !TValid) {
        if (!nValid && nInput) nInput.focus();
        else if (!TValid && TInput) TInput.focus();

        // Remove existing global error if any
        const existingError = resultsContainer.querySelector('.error-message');
        if (existingError) existingError.remove();

        return; // Validation handled by inline errors
    }

    const n = parseFloat(nInput.value);
    const T = parseFloat(TInput.value);

    setLoading(btn, resultsContainer, true);

    try {
        // Optimization: Batch API calls
        const res = await fetch(`/api/plasma/parameters?n=${n}&T_ev=${T}`);

        if (!res.ok) throw new Error();

        const data = await res.json();

        document.getElementById('res-debye').innerText = data.debye_length.toExponential(2) + " m";
        document.getElementById('res-freq').innerText = (data.plasma_frequency / (2 * Math.PI)).toExponential(2) + " Hz";
    } catch (e) {
        showError(resultsContainer, "Calculation failed.");
        document.getElementById('res-debye').innerText = "-";
        document.getElementById('res-freq').innerText = "-";
    } finally {
        setLoading(btn, resultsContainer, false);
    }
}

// Sunspot Logic
// Optimization: Cache sunspot data locally
// This eliminates redundant network requests and server-side recalculations.
const sunspotCache = {};

function updateSunspotVisuals(ratio) {
    // Visual update
    const visual = document.getElementById('sunspot-visual');
    if (!visual) return;

    // Max brightness (ratio 1) -> #ffcc00 (RGB 255, 204, 0)
    // We scale the color based on ratio.
    const r = Math.floor(255 * ratio);
    const g = Math.floor(204 * ratio);
    visual.style.backgroundColor = `rgb(${r}, ${g}, 0)`;
    visual.style.boxShadow = `0 0 20px rgb(${r}, ${Math.floor(g * 0.8)}, 0)`;

    // Update accessibility label
    visual.setAttribute('aria-label', `Sunspot visualization with intensity ratio ${ratio}`);
}

async function fetchSunspotData(ratio) {
    const tempDisplay = document.getElementById('sunspot-temp');
    if (!tempDisplay) return;

    // Check cache FIRST to avoid loading state and network request
    if (sunspotCache[ratio]) {
        const temp = sunspotCache[ratio];
        tempDisplay.textContent = temp + " K";
        tempDisplay.style.color = '';
        tempDisplay.setAttribute('aria-busy', 'false');

        const visual = document.getElementById('sunspot-visual');
        if (visual) {
            visual.setAttribute('aria-label', `Sunspot visualization with intensity ratio ${ratio}, estimated temperature ${temp} K`);
        }
        return;
    }

    try {
        const res = await fetch(`/api/solar/sunspot?ratio=${ratio}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        const temp = Math.round(data.temperature_k);

        // Save to cache
        sunspotCache[ratio] = temp;

        tempDisplay.textContent = temp + " K";
        tempDisplay.style.color = '';
        tempDisplay.setAttribute('aria-busy', 'false');

        // Enhance aria-label with temperature once loaded
        const visual = document.getElementById('sunspot-visual');
        if (visual) {
            visual.setAttribute('aria-label', `Sunspot visualization with intensity ratio ${ratio}, estimated temperature ${temp} K`);
        }
    } catch (e) {
        console.error(e);
        tempDisplay.textContent = 'Error';
        tempDisplay.style.color = '#ff6b6b';
        tempDisplay.setAttribute('aria-busy', 'false');
    }
}

// Optimization: Debounce the API call to avoid flooding the server on slider input
// debounce is defined in js/magnetosphere.js, which must be loaded before this script
let debouncedFetchSunspot;

function syncSunspot(source) {
    const slider = document.getElementById('sunspot-ratio');
    const numInput = document.getElementById('sunspot-ratio-num');

    if (!slider || !numInput) return;

    let val = parseFloat(source.value);

    if (isNaN(val)) return;
    if (val < 0.01) val = 0.01;
    if (val > 1.0) val = 1.0;

    if (source === slider) {
        numInput.value = val;
    } else {
        slider.value = val;
    }

    // Immediate visual feedback
    updateSunspotVisuals(val);

    // Check cache before showing loading state
    if (sunspotCache[val]) {
        fetchSunspotData(val); // This will just use the cache instantly
    } else {
        // Show loading state
        const tempDisplay = document.getElementById('sunspot-temp');
        if (tempDisplay && tempDisplay.getAttribute('aria-busy') !== 'true') {
             // 🛡️ Sentinel: Prevent XSS by using textContent and createElement instead of innerHTML
             tempDisplay.textContent = ' Calculating...';
             const spinner = document.createElement('span');
             spinner.className = 'loading-spinner';
             spinner.setAttribute('aria-hidden', 'true');
             tempDisplay.prepend(spinner);

             tempDisplay.setAttribute('aria-busy', 'true');
        }

        // Debounced API call
        if (debouncedFetchSunspot) {
            debouncedFetchSunspot(val);
        } else {
            // Fallback if debounce not ready (though it should be)
            fetchSunspotData(val);
        }
    }
}

// Aurora Logic
async function calcAurora(btn) {
    const resultsContainer = document.getElementById('aurora-results');
    const EInput = document.getElementById('aurora-E');
    const sigmaInput = document.getElementById('aurora-sigma');
    const areaInput = document.getElementById('aurora-area');

    const EValid = validateInput(EInput);
    const sigmaValid = validateInput(sigmaInput);
    const areaValid = validateInput(areaInput);

    if (!EValid || !sigmaValid || !areaValid) {
         if (!EValid && EInput) EInput.focus();
         else if (!sigmaValid && sigmaInput) sigmaInput.focus();
         else if (!areaValid && areaInput) areaInput.focus();

         // Remove existing global error if any
         const existingError = resultsContainer.querySelector('.error-message');
         if (existingError) existingError.remove();

         return; // Validation handled by inline errors
    }

    const E_val = parseFloat(EInput.value);
    const sigma = parseFloat(sigmaInput.value);
    const area_val = parseFloat(areaInput.value);

    setLoading(btn, resultsContainer, true);

    try {
        const res = await fetch('/api/aurora/power', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                E_field: E_val * 1e-3,
                sigma_P: sigma,
                area: area_val * 1e10
            })
        });

        if (!res.ok) throw new Error();
        const data = await res.json();

        let powerStr = data.dissipated_power.toExponential(2) + " W";
        if (data.dissipated_power > 1e9) powerStr = (data.dissipated_power / 1e9).toFixed(2) + " GW";

        document.getElementById('res-power').innerText = powerStr;
        document.getElementById('res-current').innerText = data.sheet_current.toFixed(2) + " A/m";
    } catch (e) {
        showError(resultsContainer, "Calculation failed.");
        document.getElementById('res-power').innerText = "-";
        document.getElementById('res-current').innerText = "-";
    } finally {
        setLoading(btn, resultsContainer, false);
    }
}

// Helper function to enable Enter key for triggering buttons
function enableEnterKey(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (!input || !btn) return;

    // Add tooltip to make shortcut discoverable
    if (!input.hasAttribute('title')) {
        input.setAttribute('title', 'Press Enter to calculate');
    }

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission behavior
            btn.click();
        }
    });
}

// Copy to Clipboard Helper
function copyToClipboard(el) {
    if (el.getAttribute('aria-busy') === 'true') return;

    // Get text, cleaning up any potential spinner text if hidden but still in DOM
    const text = el.innerText.trim();
    if (!text || text === '-' || text.includes('Calculating')) return;

    navigator.clipboard.writeText(text).then(() => {
        // Visual Feedback
        el.classList.add('copied');
        el.setAttribute('title', 'Copied!');

        // Screen reader feedback
        const announcer = document.getElementById('sr-announcer');
        if (announcer) {
            announcer.textContent = `Copied ${text} to clipboard`;
            // Clear after announcement to allow repeated announcements
            setTimeout(() => { announcer.textContent = ''; }, 3000);
        }

        setTimeout(() => {
            el.classList.remove('copied');
            el.setAttribute('title', el.dataset.originalTitle || "Click to copy result");
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

function initCopyableResults() {
    const results = document.querySelectorAll('.copyable-result');
    results.forEach(el => {
        // Store original title for restoration
        el.dataset.originalTitle = el.getAttribute('title') || "Click to copy result";

        el.addEventListener('click', () => copyToClipboard(el));
        el.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                copyToClipboard(el);
            }
        });
    });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initCopyableResults();
    // Initialize debounce if available
    if (typeof debounce === 'function') {
        debouncedFetchSunspot = debounce(fetchSunspotData, 300);
    } else {
        console.warn('debounce function not found. Falling back to direct calls.');
        debouncedFetchSunspot = fetchSunspotData;
    }

    // Stale state handler
    function markStale(e) {
        const inputId = e.target.id;
        let resultsId = null;
        let btnId = null;

        if (inputId.startsWith('plasma-')) {
            resultsId = 'plasma-results';
            btnId = 'btn-calc-plasma';
        } else if (inputId.startsWith('aurora-')) {
            resultsId = 'aurora-results';
            btnId = 'btn-calc-aurora';
        }

        if (resultsId && btnId) {
            const resultsEl = document.getElementById(resultsId);
            const btnEl = document.getElementById(btnId);
            if (resultsEl) resultsEl.classList.add('stale-results');
            if (btnEl) btnEl.classList.add('needs-update');
        }
    }

    // Attach listeners for auto-clearing errors and validation on blur
    ['plasma-n', 'plasma-T', 'aurora-E', 'aurora-sigma', 'aurora-area'].forEach(id => {
         const el = document.getElementById(id);
         if(el) {
             el.addEventListener('input', clearErrorState);
             el.addEventListener('input', markStale);
             el.addEventListener('blur', () => validateInput(el));
         }
    });

    // Plasma Button
    const btnPlasma = document.getElementById('btn-calc-plasma');
    if (btnPlasma) {
        btnPlasma.addEventListener('click', (e) => {
             // If clicked on icon inside button, target might be span. Find closest button.
             const btn = e.target.closest('button');
             if (btn) calcPlasma(btn);
        });
    }

    // Aurora Button
    const btnAurora = document.getElementById('btn-calc-aurora');
    if (btnAurora) {
        btnAurora.addEventListener('click', (e) => {
             const btn = e.target.closest('button');
             if (btn) calcAurora(btn);
        });
    }

    // Sunspot Inputs
    const sunspotSlider = document.getElementById('sunspot-ratio');
    const sunspotNum = document.getElementById('sunspot-ratio-num');

    if (sunspotSlider) {
        sunspotSlider.addEventListener('input', (e) => syncSunspot(e.target));
    }
    if (sunspotNum) {
        sunspotNum.addEventListener('input', (e) => syncSunspot(e.target));
    }

    // Initial calculations
    calcPlasma(null);
    calcAurora(null);

    // Auto-select text in inputs on focus for easier overwriting
    document.querySelectorAll('.glass-input[type="number"]').forEach(input => {
        input.addEventListener('focus', function() {
            this.select();
        });
    });

    // Enable Enter key for better keyboard accessibility
    enableEnterKey('plasma-n', 'btn-calc-plasma');
    enableEnterKey('plasma-T', 'btn-calc-plasma');
    enableEnterKey('aurora-E', 'btn-calc-aurora');
    enableEnterKey('aurora-sigma', 'btn-calc-aurora');
    enableEnterKey('aurora-area', 'btn-calc-aurora');

    if (sunspotSlider) {
        syncSunspot(sunspotSlider);
    }
});
