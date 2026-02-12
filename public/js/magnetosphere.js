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

async function updateMagnetosphere() {
    const densityElement = document.getElementById('sw-density');
    const velocityElement = document.getElementById('sw-velocity');

    if (!densityElement || !velocityElement) return;

    const density = densityElement.value * 1e6; // cm-3 to m-3
    const velocity = velocityElement.value * 1e3; // km/s to m/s

    try {
        const response = await fetch(`/api/magnetosphere/standoff?density=${density}&velocity=${velocity}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        const standoff = data.radius_re;

        const display = document.getElementById('standoff-display');
        if (display) display.innerText = standoff.toFixed(1) + " Re";

        drawMagnetosphere(standoff);
    } catch (error) {
        console.error('Error fetching magnetosphere data:', error);
    }
}

function drawMagnetosphere(standoff) {
    const container = d3.select("#magnetosphere-viz");
    if (container.empty()) return;

    container.selectAll("*").remove(); // Clear previous

    const width = container.node().getBoundingClientRect().width || 400;
    const height = container.node().getBoundingClientRect().height || 300;

    const svg = container.append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${width} ${height}`);

    const centerX = width * 0.7;
    const centerY = height / 2;

    // Scale: Fit roughly 20 Re in half width
    const scale = (width * 0.4) / 20;

    // Draw Earth
    svg.append("circle")
        .attr("cx", centerX)
        .attr("cy", centerY)
        .attr("r", 1 * scale) // Earth radius = 1 Re
        .attr("fill", "#0044ff")
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 1);

    // Draw Magnetopause (Approximate Parabola)
    // x = -standoff + k * y^2
    // k = 1 / (2.25 * standoff) for flank at 1.5 * standoff

    const curveData = [];
    const k = 1 / (2.25 * standoff);

    // Generate points
    for (let y = -25; y <= 25; y+=0.5) {
        const x_re = -standoff + k * y * y;

        // Only draw if x < 10 (don't go too far behind Earth)
        if (x_re < 15) {
            curveData.push({x: x_re, y: y});
        }
    }

    const line = d3.line()
        .x(d => centerX + d.x * scale)
        .y(d => centerY + d.y * scale)
        .curve(d3.curveBasis);

    svg.append("path")
        .datum(curveData)
        .attr("fill", "none")
        .attr("stroke", "#ffaa00")
        .attr("stroke-width", 2)
        .attr("filter", "drop-shadow(0 0 5px #ffaa00)")
        .attr("d", line);

    // Draw Sun direction arrow
    const arrowStart = 20;
    const arrowEnd = centerX - standoff * scale - 20;

    if (arrowEnd > arrowStart) {
        svg.append("defs").append("marker")
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

        svg.append("line")
            .attr("x1", arrowStart)
            .attr("y1", centerY)
            .attr("x2", arrowEnd)
            .attr("y2", centerY)
            .attr("stroke", "#ffaa00")
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrow)");

        svg.append("text")
            .attr("x", arrowStart)
            .attr("y", centerY - 10)
            .attr("fill", "#ffaa00")
            .attr("font-size", "12px")
            .text("Solar Wind");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const densityInput = document.getElementById('sw-density');
    const velocityInput = document.getElementById('sw-velocity');

    // Create a debounced version of the update function
    const debouncedUpdate = debounce(updateMagnetosphere, 300);

    if (densityInput) {
        densityInput.addEventListener('input', (e) => {
            document.getElementById('density-val').innerText = e.target.value;
            debouncedUpdate();
        });
    }

    if (velocityInput) {
        velocityInput.addEventListener('input', (e) => {
            document.getElementById('velocity-val').innerText = e.target.value;
            debouncedUpdate();
        });
    }

    updateMagnetosphere();
});
