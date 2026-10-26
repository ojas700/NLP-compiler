// ==========================================================================
// NLP COMPILER — Landing Page Interactive Scripts
// Walkthrough Controller, Scroll Storytelling Timeline & Theme Sync
// ==========================================================================

window.landingScriptLoaded = true;

if (window.__landingInitialized) {
    console.warn('[Landing] landing.js already initialized, skipping duplicate execution.');
} else {
    window.__landingInitialized = true;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLandingApp);
    } else {
        initLandingApp();
    }
}

function initLandingApp() {
    // 1. Theme Toggle (Sync with localStorage)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const savedTheme = localStorage.getItem('app-theme') || 'dark';
        applyTheme(savedTheme);

        themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
            const targetTheme = (currentTheme === 'light') ? 'dark' : 'light';
            applyTheme(targetTheme);
            localStorage.setItem('app-theme', targetTheme);
        });
    }

    function applyTheme(theme) {
        if (theme === 'light') {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            updateThemeIcon('light');
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            updateThemeIcon('dark');
        }
    }

    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        if (theme === 'light') {
            themeToggle.innerHTML = `<svg class="theme-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
            themeToggle.title = "Switch to Dark Mode";
        } else {
            themeToggle.innerHTML = `<svg class="theme-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`;
            themeToggle.title = "Switch to Light Mode";
        }
    }

    // 2. Interactive Pipeline Walkthrough Carousel
    const stages = document.querySelectorAll('.walkthrough-stage');
    const prevBtn = document.getElementById('wt-prev');
    const nextBtn = document.getElementById('wt-next');
    const indicator = document.getElementById('wt-indicator');
    let currentStep = 1;
    const totalSteps = stages.length;

    function updateWalkthrough(step) {
        if (step < 1) step = 1;
        if (step > totalSteps) step = totalSteps;
        currentStep = step;

        stages.forEach(st => {
            if (parseInt(st.getAttribute('data-step')) === currentStep) {
                st.classList.add('active');
            } else {
                st.classList.remove('active');
            }
        });

        if (indicator) indicator.textContent = `Stage ${currentStep} of ${totalSteps}`;
        if (prevBtn) prevBtn.disabled = (currentStep === 1);
        if (nextBtn) nextBtn.disabled = (currentStep === totalSteps);
    }

    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', () => updateWalkthrough(currentStep - 1));
        nextBtn.addEventListener('click', () => updateWalkthrough(currentStep + 1));
        updateWalkthrough(1);
    }

    // 3. Smooth In-Page Anchor Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // 4. Scroll Reveal Animations (Intersection Observer)
    if ('IntersectionObserver' in window) {
        const revealElements = document.querySelectorAll('.scroll-reveal');
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    obs.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -40px 0px'
        });

        revealElements.forEach(el => observer.observe(el));

        // 5. Timeline Storytelling Progress Fill
        const timelineWrapper = document.querySelector('.story-timeline-wrapper');
        const timelineProgress = document.getElementById('timeline-progress');
        const stageCards = document.querySelectorAll('.stage-card');

        if (timelineWrapper && timelineProgress) {
            const updateTimeline = () => {
                const rect = timelineWrapper.getBoundingClientRect();
                const windowHeight = window.innerHeight;
                
                // Progress from top entering window to bottom leaving
                const start = windowHeight * 0.75;
                const total = rect.height;
                const current = start - rect.top;

                let pct = (current / total) * 100;
                if (pct < 0) pct = 0;
                if (pct > 100) pct = 100;

                timelineProgress.style.height = `${pct}%`;

                // Highlight active stages based on position:
                // All reached stages stay selected until scrolling back up past them
                stageCards.forEach(card => {
                    const cRect = card.getBoundingClientRect();
                    if (cRect.top < windowHeight * 0.70) {
                        card.classList.add('stage-active');
                    } else {
                        card.classList.remove('stage-active');
                    }
                });
            };

            window.addEventListener('scroll', updateTimeline, { passive: true });
            window.addEventListener('resize', updateTimeline, { passive: true });
            updateTimeline();
        }
    }
}
