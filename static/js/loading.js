(function () {
    var loader = document.getElementById('loading-overlay');
    var progressBar = document.querySelector('#loading-bar .progress');
    var loadingText = document.getElementById('loading-text');
    if (!loader || !progressBar) return;

    var width = 0;
    var interval;
    var dotsInterval;
    var isLoading = false;
    var currentMessage = 'Loading';

    function startProgress(message) {
        if (isLoading) return;
        isLoading = true;
        loader.style.display = 'flex';
        width = 0;
        progressBar.style.width = '0%';
        currentMessage = message || 'Loading';
        if (loadingText) loadingText.textContent = currentMessage;
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
            loadingText.textContent = currentMessage + new Array(dots + 1).join('.');
        }, 500);
    }

    function updateProgress(current, total, message) {
        if (!isLoading) startProgress();
        if (typeof total === 'number' && total > 0) {
            width = Math.min(100, (current / total) * 100);
            progressBar.style.width = width + '%';
        }
        if (message) {
            currentMessage = message;
            if (loadingText) loadingText.textContent = currentMessage;
        }
    }

    function hideProgress() {
        if (!isLoading) {
            loader.style.display = 'none';
            progressBar.style.width = '0%';
            return;
        }
        isLoading = false;
        clearInterval(interval);
        clearInterval(dotsInterval);
        loader.style.display = 'none';
        progressBar.style.width = '0%';
        currentMessage = 'Loading';
        if (loadingText) loadingText.textContent = currentMessage;
    }

    // Expose control helpers for manual updates
    window.loadingOverlay = {
        start: startProgress,
        update: updateProgress,
        done: hideProgress
    };

    // Progress bar starts on navigation events only
    // Removed automatic start on page load to prevent duplicate flashes
    window.addEventListener('beforeunload', function () { startProgress(); });

    window.addEventListener('pageshow', hideProgress);

    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
        links[i].addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            if (!href || href.charAt(0) === '#' || this.target === '_blank') return;
            startProgress();
        });
    }
})();

