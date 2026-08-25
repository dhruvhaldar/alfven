// Lightweight, dependency-free animated starfield.
(() => {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d', { alpha: true });
    if (!context) return;

    canvas.setAttribute('aria-hidden', 'true');
    container.appendChild(canvas);

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const palette = [
        [68, 221, 255],
        [255, 255, 255],
        [168, 128, 255],
        [255, 190, 92]
    ];

    let width = 0;
    let height = 0;
    let pixelRatio = 1;
    let stars = [];
    let animationId = null;
    let lastFrame = 0;

    function makeStar(randomY = true) {
        const depth = Math.random();
        return {
            x: Math.random() * width,
            y: randomY ? Math.random() * height : -4,
            radius: 0.45 + depth * 1.35,
            speed: 2.5 + depth * 10,
            phase: Math.random() * Math.PI * 2,
            twinkle: 0.45 + Math.random() * 1.1,
            color: palette[Math.floor(Math.random() * palette.length)]
        };
    }

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

        canvas.width = Math.round(width * pixelRatio);
        canvas.height = Math.round(height * pixelRatio);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);

        const density = width <= 768 ? 0.00032 : 0.0002;
        const starCount = Math.max(180, Math.min(520, Math.round(width * height * density)));
        stars = Array.from({ length: starCount }, () => makeStar(true));
    }

    function draw(timestamp) {
        const elapsed = Math.min((timestamp - lastFrame) / 1000 || 0, 0.05);
        lastFrame = timestamp;
        const motionScale = prefersReducedMotion.matches ? 0.18 : 1;

        context.clearRect(0, 0, width, height);

        for (const star of stars) {
            star.y += star.speed * elapsed * motionScale;
            if (star.y > height + 4) Object.assign(star, makeStar(false));

            const pulse = 0.58 + Math.sin(timestamp * 0.001 * star.twinkle + star.phase) * 0.28;
            const [red, green, blue] = star.color;

            context.beginPath();
            context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${pulse})`;
            context.shadowColor = `rgba(${red}, ${green}, ${blue}, 0.65)`;
            context.shadowBlur = star.radius > 1.25 ? 5 : 2;
            context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            context.fill();
        }

        context.shadowBlur = 0;
        animationId = requestAnimationFrame(draw);
    }

    function handleVisibilityChange() {
        if (document.hidden && animationId !== null) {
            cancelAnimationFrame(animationId);
            animationId = null;
        } else if (!document.hidden && animationId === null) {
            lastFrame = 0;
            animationId = requestAnimationFrame(draw);
        }
    }

    resize();
    window.addEventListener('resize', resize, { passive: true });
    document.addEventListener('visibilitychange', handleVisibilityChange);
    animationId = requestAnimationFrame(draw);
})();
