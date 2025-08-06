(function () {
    const loader = document.getElementById('loading-overlay');
    const progressBar = document.querySelector('#loading-bar .progress');
    const loadingText = document.getElementById('loading-text');
    if (!loader || !progressBar) return;

    let width = 0;
    let interval;
    let dotsInterval;

    function startProgress() {
        loader.style.display = 'flex';
        width = 0;
        progressBar.style.width = '0%';
        if (loadingText) loadingText.textContent = 'Loading';
        clearInterval(interval);
        clearInterval(dotsInterval);
        interval = setInterval(() => {
            width = Math.min(width + Math.random() * 20, 90);
            progressBar.style.width = width + '%';
        }, 200);
        let dots = 0;
        dotsInterval = setInterval(() => {
            if (!loadingText) return;
            dots = (dots + 1) % 4;
            loadingText.textContent = 'Loading' + '.'.repeat(dots);
        }, 500);
    }

    function stopProgress() {
        clearInterval(interval);
        clearInterval(dotsInterval);
        progressBar.style.width = '100%';
        setTimeout(() => {
            loader.style.display = 'none';
            if (loadingText) loadingText.textContent = 'Loading';
        }, 300);
    }

    startProgress();
    window.addEventListener('load', stopProgress);
    window.addEventListener('beforeunload', startProgress);

    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', e => {
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || link.target === '_blank') return;
            startProgress();
        });
    });
})();
