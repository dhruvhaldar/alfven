// public/js/magnetosphere.js

/**
 * Debounce function to limit the rate at which a function can fire.
 * Improves performance by preventing excessive API calls and re-renders during rapid input events.
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimization: Cache standoff data locally since there's a small discrete set of inputs
// This eliminates redundant network requests and server-side recalculations.
const magnetosphereCache = {};

async function updateMagnetosphere() {
    const densityElement = document.getElementById('sw-density');
    const velocityElement = document.getElementById('sw-velocity');

    if (!densityElement || !velocityElement) return;

    const density = densityElement.value * 1e6; // cm-3 to m-3
    const velocity = velocityElement.value * 1e3; // km/s to m/s
    const cacheKey = `${density}_${velocity}`;

    const display = document.getElementById('standoff-display');

    // Check cache FIRST to avoid loading state and network request
    if (magnetosphereCache[cacheKey]) {
        const standoff = magnetosphereCache[cacheKey];
        if (display) {
             display.innerText = standoff.toFixed(1) + " Re";
             display.style.color = '';
             display.style.fontSize = '';
             display.setAttribute('aria-busy', 'false');
        }
        drawMagnetosphere(standoff);
        return;
    }

    try {
        const response = await fetch(`/api/magnetosphere/standoff?density=${density}&velocity=${velocity}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        const standoff = data.radius_re;

        // Save to cache
        magnetosphereCache[cacheKey] = standoff;

        if (display) {
             display.innerText = standoff.toFixed(1) + " Re";
             display.style.color = '';
             display.style.fontSize = '';
             display.setAttribute('aria-busy', 'false');
        }

        drawMagnetosphere(standoff);
    } catch (error) {
        console.error('Error fetching magnetosphere data:', error);
        const display = document.getElementById('standoff-display');
        if (display) {
             display.textContent = '⚠️ Error';
             display.style.color = '#ff6b6b';
             display.style.fontSize = '1rem';
             display.setAttribute('aria-busy', 'false');
        }
    }
}

let cachedVizWidth = 0;
let cachedVizHeight = 0;

function updateVizDimensions() {
    const container = document.getElementById("magnetosphere-viz");
    if (container) {
        const rect = container.getBoundingClientRect();
        cachedVizWidth = rect.width || 400;
        cachedVizHeight = rect.height || 300;
    }
}

// Update dimensions on resize to keep SVG responsive
window.addEventListener('resize', () => {
    // Debounce the resize slightly if needed, but for dimensions it's usually okay.
    updateVizDimensions();
});

function drawMagnetosphere(standoff) {
    const container = d3.select("#magnetosphere-viz");
    if (container.empty()) return;

    if (cachedVizWidth === 0 || cachedVizHeight === 0) {
        updateVizDimensions();
    }

    // Optimization: Reuse existing SVG and cache dimensions to prevent DOM layout thrashing
    const width = cachedVizWidth;
    const height = cachedVizHeight;
    const centerX = width * 0.7;
    const centerY = height / 2;
    // Scale: Fit roughly 20 Re in half width
    const scale = (width * 0.4) / 20;

    // 1. Setup SVG and static elements if they don't exist
    let svg = container.select("svg");
    if (svg.empty()) {
        svg = container.append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("role", "img");

        // Static definitions
        const defs = svg.append("defs");
        defs.append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 0 10 10")
            .attr("refX", 5)
            .attr("refY", 5)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto-start-reverse")
            .append("path")
            .attr("d", "M 0 0 L 10 5 L 0 10 z")
            .attr("fill", "#ffaa00");

        // Earth (static shape, dynamic position)
        svg.append("circle")
            .attr("class", "earth")
            .attr("fill", "#0044ff")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 1);

        // Magnetopause path (dynamic shape)
        svg.append("path")
            .attr("class", "magnetopause")
            .attr("fill", "none")
            .attr("stroke", "#ffaa00")
            .attr("stroke-width", 2)
            .attr("filter", "drop-shadow(0 0 5px #ffaa00)");

        // Arrow line
        svg.append("line")
             .attr("class", "solar-wind-arrow")
             .attr("stroke", "#ffaa00")
             .attr("stroke-width", 2)
             .attr("marker-end", "url(#arrow)");

        // Arrow text
        svg.append("text")
             .attr("class", "solar-wind-text")
             .attr("fill", "#ffaa00")
             .attr("font-size", "12px")
             .text("Solar Wind");
    }

    // 2. Update Attributes for all elements
    svg.attr("viewBox", `0 0 ${width} ${height}`)
       .attr("aria-label", `Magnetosphere visualization. Standoff distance is ${standoff.toFixed(1)} Earth Radii.`);

    // Update Earth
    svg.select(".earth")
        .attr("cx", centerX)
        .attr("cy", centerY)
        .attr("r", 1 * scale);

    // Calculate Magnetopause Curve
    // x = -standoff + k * y^2
    const curveData = [];
    const k = 1 / (2.25 * standoff);

    // Generate points
    for (let y = -25; y <= 25; y+=0.5) {
        const x_re = -standoff + k * y * y;
        // Only draw if x < 15 (don't go too far behind Earth)
        if (x_re < 15) {
            curveData.push({x: x_re, y: y});
        }
    }

    const line = d3.line()
        .x(d => centerX + d.x * scale)
        .y(d => centerY + d.y * scale)
        .curve(d3.curveBasis);

    svg.select(".magnetopause")
        .datum(curveData)
        .attr("d", line);

    // Update Arrow
    const arrowStart = 20;
    const arrowEnd = centerX - standoff * scale - 20;

    const arrowLine = svg.select(".solar-wind-arrow");
    const arrowText = svg.select(".solar-wind-text");

    if (arrowEnd > arrowStart) {
        arrowLine
            .attr("display", null)
            .attr("x1", arrowStart)
            .attr("y1", centerY)
            .attr("x2", arrowEnd)
            .attr("y2", centerY);

        arrowText
            .attr("display", null)
            .attr("x", arrowStart)
            .attr("y", centerY - 10);
    } else {
        arrowLine.attr("display", "none");
        arrowText.attr("display", "none");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const densityInput = document.getElementById('sw-density');
    const velocityInput = document.getElementById('sw-velocity');
    const densityNum = document.getElementById('sw-density-num');
    const velocityNum = document.getElementById('sw-velocity-num');

    // Initialize dimensions on load
    updateVizDimensions();

    // Create a debounced version of the update function
    const debouncedUpdate = debounce(updateMagnetosphere, 300);

    function setLoadingState() {
        const display = document.getElementById('standoff-display');
        // Optimization: Prevent DOM thrashing by checking aria-busy state
        if (display && display.getAttribute('aria-busy') !== 'true') {
             // 🛡️ Sentinel: Prevent XSS by using textContent and createElement instead of innerHTML
             display.textContent = ' Calculating...';
             const spinner = document.createElement('span');
             spinner.className = 'loading-spinner';
             spinner.setAttribute('aria-hidden', 'true');
             display.prepend(spinner);
             display.setAttribute('aria-busy', 'true');
        }
    }

    // Optimization: Check cache synchronously during rapid events (like slider drag)
    // to prevent DOM thrashing and visual delays before debouncing
    function triggerUpdate(density, velocity) {
        const cacheKey = `${density * 1e6}_${velocity * 1e3}`;
        if (magnetosphereCache[cacheKey]) {
            // Update immediately if cached
            updateMagnetosphere();
        } else {
            setLoadingState();
            debouncedUpdate();
        }
    }

    function updateFromRange(rangeInput, numberInput) {
        numberInput.value = rangeInput.value;
        numberInput.classList.remove('invalid');
        numberInput.setAttribute('aria-invalid', 'false');
        const density = parseFloat(document.getElementById('sw-density-num').value);
        const velocity = parseFloat(document.getElementById('sw-velocity-num').value);
        triggerUpdate(density, velocity);
    }

    function updateFromNumber(numberInput, rangeInput) {
        const val = parseFloat(numberInput.value);
        const min = parseFloat(numberInput.min);
        const max = parseFloat(numberInput.max);

        // Allow partial typing, but don't update if invalid
        if (isNaN(val) || val < min || val > max) {
            numberInput.classList.add('invalid');
            numberInput.setAttribute('aria-invalid', 'true');
            return;
        }

        numberInput.classList.remove('invalid');
        numberInput.setAttribute('aria-invalid', 'false');
        rangeInput.value = val;
        const density = parseFloat(document.getElementById('sw-density-num').value);
        const velocity = parseFloat(document.getElementById('sw-velocity-num').value);
        triggerUpdate(density, velocity);
    }

    function clampNumberInput(numberInput, rangeInput) {
        let val = parseFloat(numberInput.value);
        const min = parseFloat(numberInput.min);
        const max = parseFloat(numberInput.max);

        if (isNaN(val)) val = min;
        if (val < min) val = min;
        if (val > max) val = max;

        numberInput.value = val;
        numberInput.classList.remove('invalid');
        numberInput.setAttribute('aria-invalid', 'false');

        // Only update if effective change or to ensure sync
        if (rangeInput.value != val) {
            rangeInput.value = val;
            const density = parseFloat(document.getElementById('sw-density-num').value);
            const velocity = parseFloat(document.getElementById('sw-velocity-num').value);
            triggerUpdate(density, velocity);
        }
    }

    if (densityInput && densityNum) {
        densityInput.addEventListener('input', () => updateFromRange(densityInput, densityNum));
        densityNum.addEventListener('input', () => updateFromNumber(densityNum, densityInput));
        densityNum.addEventListener('change', () => clampNumberInput(densityNum, densityInput));
    }

    if (velocityInput && velocityNum) {
        velocityInput.addEventListener('input', () => updateFromRange(velocityInput, velocityNum));
        velocityNum.addEventListener('input', () => updateFromNumber(velocityNum, velocityInput));
        velocityNum.addEventListener('change', () => clampNumberInput(velocityNum, velocityInput));
    }

    updateMagnetosphere();
});
