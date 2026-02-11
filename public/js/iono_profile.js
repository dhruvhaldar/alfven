// public/js/iono_profile.js
let chart;

async function updateIonosphere() {
    const toggle = document.getElementById('day-night-toggle');
    if (!toggle) return;

    const isDay = toggle.checked;

    // Layers
    // F-layer: h0=300km, H=50km, n_max=1e12
    // E-layer: h0=110km, H=10km, n_max=1e11 (weaker at night)
    // D-layer: h0=80km, H=5km, n_max=1e10 (only day)

    const layers = [];

    // F Layer
    layers.push({h0: 300, H: 50, n_max: isDay ? 1e12 : 0.5e12});

    // E Layer
    layers.push({h0: 110, H: 10, n_max: isDay ? 1e11 : 1e9});

    // D Layer (Day only)
    if (isDay) {
        layers.push({h0: 80, H: 5, n_max: 1e10});
    }

    const payload = {
        layers: layers,
        min_h: 60,
        max_h: 600,
        steps: 200
    };

    try {
        const response = await fetch('/api/ionosphere/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        drawChart(data);
    } catch (error) {
        console.error('Error fetching ionosphere data:', error);
    }
}

function drawChart(data) {
    const canvas = document.getElementById('iono-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (chart) {
        chart.destroy();
    }

    // Prepare data points {x: altitude, y: density}
    // Note: Usually profile is plotted with Altitude on Y and Density on X.
    // But standard charts put independent variable on X.
    // The proposal artifact says "Electron Density vs Altitude". Usually Altitude is Y.
    // Let's swap axis?
    // If Altitude is Y, then X is Density (Log).
    // Let's do that.

    const points = data.altitude.map((h, i) => ({x: data.density[i], y: h}));

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Electron Density',
                data: points,
                borderColor: '#4df',
                backgroundColor: 'rgba(68, 221, 255, 0.2)',
                borderWidth: 2,
                fill: true, // Fill area under line? For vertical profile, maybe fill to left?
                fill: 'origin',
                pointRadius: 0,
                tension: 0.4,
                showLine: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // Make vertical chart (Y is independent variable effectively)
            scales: {
                x: {
                    type: 'logarithmic', // Density on X
                    title: {
                        display: true,
                        text: 'Density (m^-3)',
                        color: '#eee'
                    },
                    ticks: {
                        color: '#eee',
                        callback: function(value, index, values) {
                            return Number(value).toExponential();
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    type: 'linear', // Altitude on Y
                    title: {
                        display: true,
                        text: 'Altitude (km)',
                        color: '#eee'
                    },
                    ticks: {
                        color: '#eee'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#eee'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x.toExponential(2) + ' m^-3';
                        }
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('day-night-toggle');
    if (toggle) {
        toggle.addEventListener('change', updateIonosphere);
    }
    updateIonosphere();
});
