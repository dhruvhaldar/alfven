// tests/measure_debounce.js

// Mock implementation of debounce for testing the concept
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

// Mock function to represent updateMagnetosphere
let callCount = 0;
function updateMagnetosphere() {
    callCount++;
}

// Without Debounce Simulation
callCount = 0;
console.log("Simulating rapid input events WITHOUT debounce...");
for (let i = 0; i < 100; i++) {
    updateMagnetosphere(); // Called on every event
}
console.log(`Calls made: ${callCount} (Expected: 100)`);

// With Debounce Simulation
callCount = 0;
const debouncedUpdate = debounce(updateMagnetosphere, 300);

console.log("\nSimulating rapid input events WITH debounce (300ms)...");
// Simulate rapid events (faster than 300ms)
for (let i = 0; i < 100; i++) {
    debouncedUpdate();
    // In real browser, time passes. Here we simulate synchronous burst.
}

// Wait for debounce to trigger
setTimeout(() => {
    console.log(`Calls made: ${callCount} (Expected: 1)`);
    if (callCount === 1) {
        console.log("SUCCESS: Debounce correctly coalesced calls.");
    } else {
        console.error("FAILURE: Debounce logic incorrect.");
        process.exit(1);
    }
}, 500);
