// public/js/background.js
const THREE_SRC = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';

function loadThreeJs() {
    if (window.THREE) return Promise.resolve(window.THREE);

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = THREE_SRC;
        script.defer = true;
        script.crossOrigin = 'anonymous';
        script.integrity = 'sha384-CI3ELBVUz9XQO+97x6nwMDPosPR5XvsxW2ua7N1Xeygeh1IxtgqtCkGfQY9WWdHu';
        script.onload = () => resolve(window.THREE);
        script.onerror = () => reject(new Error('Failed to load Three.js'));
        document.head.appendChild(script);
    });
}

let scene, camera, renderer, stars, particles;
let animationId; // Track animation frame ID

function init() {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    scene = new THREE.Scene();
    // Add fog for depth
    scene.fog = new THREE.FogExp2(0x000000, 0.001);

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.z = 500;

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    container.appendChild(renderer.domElement);

    // Create Stars
    const starGeometry = new THREE.BufferGeometry();
    const starCount = window.matchMedia("(max-width: 768px)").matches ? 2500 : 5000;
    const posArray = new Float32Array(starCount * 3);
    const colorArray = new Float32Array(starCount * 3);

    const colors = [
        new THREE.Color(0x44ddff), // Blue
        new THREE.Color(0xffffff), // White
        new THREE.Color(0xffaa00)  // Orange
    ];

    for(let i = 0; i < starCount * 3; i+=3) {
        // Random position in a large sphere
        const r = 1000 * Math.random() + 500; // Radius between 500 and 1500
        const theta = 2 * Math.PI * Math.random();
        const phi = Math.acos(2 * Math.random() - 1);

        posArray[i] = r * Math.sin(phi) * Math.cos(theta);
        posArray[i+1] = r * Math.sin(phi) * Math.sin(theta);
        posArray[i+2] = r * Math.cos(phi);

        // Random color
        const color = colors[Math.floor(Math.random() * colors.length)];
        colorArray[i] = color.r;
        colorArray[i+1] = color.g;
        colorArray[i+2] = color.b;
    }

    starGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    starGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));

    const starMaterial = new THREE.PointsMaterial({
        size: 2,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);

    window.addEventListener('resize', onWindowResize, false);

    // Optimization: Pause animation when tab is not visible
    document.addEventListener('visibilitychange', handleVisibilityChange);

    animate();
}

function handleVisibilityChange() {
    if (document.hidden) {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    } else {
        if (!animationId) {
            animate();
        }
    }
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    animationId = requestAnimationFrame(animate);

    if (stars) {
        stars.rotation.y += 0.0002;
        stars.rotation.x += 0.0001;
    }

    renderer.render(scene, camera);
}

function scheduleInit() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const start = async () => {
        try {
            await loadThreeJs();
            init();
        } catch (error) {
            console.warn(error);
        }
    };
    if ('requestIdleCallback' in window) {
        requestIdleCallback(start, { timeout: 1500 });
    } else {
        setTimeout(start, 300);
    }
}

document.addEventListener('DOMContentLoaded', scheduleInit);
