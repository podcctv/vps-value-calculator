(function () {
    var ip = window.PROBE_IP || '';
    if (!ip) return;
    var output = document.getElementById('probe-output');
    function append(text) {
        if (!output) return;
        output.textContent += text + '\n';
    }
    var total = 2;
    var current = 0;
    loadingOverlay.start('正在进行 Ping 测试');
    fetch('/ping/' + encodeURIComponent(ip))
        .then(function (res) { return res.text(); })
        .then(function (text) {
            append('Ping 结果:\n' + text + '\n');
            current++;
            loadingOverlay.update(current, total, '正在进行 Traceroute 测试');
            return fetch('/traceroute/' + encodeURIComponent(ip));
        })
        .then(function (res) { return res.text(); })
        .then(function (text) {
            append('Traceroute 结果:\n' + text + '\n');
            current++;
            loadingOverlay.update(current, total, '测试完成');
        })
        .catch(function (err) {
            append('错误: ' + err);
        })
        .finally(function () {
            loadingOverlay.done();
        });
})();
