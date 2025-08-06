(function () {
    var loader = document.getElementById('loading-overlay');
    var progressBar = document.querySelector('#loading-bar .progress');
    var loadingText = document.getElementById('loading-text');
    if (!loader || !progressBar) return;

    var width = 0;
    var interval;
    var dotsInterval;

    function startProgress() {
        loader.style.display = 'flex';
        width = 0;
        progressBar.style.width = '0%';
        if (loadingText) loadingText.textContent = 'Loading';
        clearInterval(interval);
        clearInterval(dotsInterval);
        interval = setInterval(function () {
            width = Math.min(width + Math.random() * 20, 90);
            progressBar.style.width = width + '%';
        }, 200);
        var dots = 0;
        dotsInterval = setInterval(function () {
            if (!loadingText) return;
            dots = (dots + 1) % 4;
            loadingText.textContent = 'Loading' + new Array(dots + 1).join('.');
        }, 500);
    }

    function stopProgress() {
        clearInterval(interval);
        clearInterval(dotsInterval);
        progressBar.style.width = '100%';
        setTimeout(function () {
            loader.style.display = 'none';
            if (loadingText) loadingText.textContent = 'Loading';
        }, 300);
    }

    startProgress();
    window.addEventListener('load', stopProgress);
    window.addEventListener('beforeunload', startProgress);

    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
        links[i].addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            if (!href || href.charAt(0) === '#' || this.target === '_blank') return;
            startProgress();
        });
    }
})();

