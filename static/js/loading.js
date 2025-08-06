(function () {
    const loader = document.getElementById('loading-overlay');
    const progressBar = document.querySelector('#loading-bar .progress');
    if (!loader || !progressBar) return;

    let width = 0;
    let interval;

    function startProgress() {
        loader.style.display = 'flex';
        width = 0;
        progressBar.style.width = '0%';
        clearInterval(interval);
        interval = setInterval(() => {
            width = Math.min(width + Math.random() * 20, 90);
            progressBar.style.width = width + '%';
        }, 200);
    }

    function stopProgress() {
        clearInterval(interval);
        progressBar.style.width = '100%';
        setTimeout(() => {
            loader.style.display = 'none';
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
