(function(){
    const STATUS_IDS = {
        ping: 'ping-status',
        traceroute: 'traceroute-status',
        speedtest: 'speedtest-status'
    };

    function setStatus(id, text) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = text;
        }
    }

    async function run() {
        const tests = [
            {
                id: 'ping',
                label: 'Ping',
                run: async () => {
                    const res = await fetch('/ping/1.1.1.1');
                    return await res.text();
                }
            },
            {
                id: 'traceroute',
                label: 'Traceroute',
                run: async () => {
                    const res = await fetch('/traceroute/1.1.1.1');
                    return await res.text();
                }
            },
            {
                id: 'speedtest',
                label: 'SpeedTest',
                run: async () => {
                    const res = await fetch('/speedtest');
                    return await res.json();
                }
            }
        ];

        loadingOverlay.start('运行网络测试');

        for (let i = 0; i < tests.length; i++) {
            const t = tests[i];
            const statusId = STATUS_IDS[t.id];
            setStatus(statusId, t.label + '：测试中...');
            try {
                const result = await t.run();
                let text = t.label + '：完成';
                if (t.id === 'speedtest') {
                    if (result.download && result.upload) {
                        text += ` (下行 ${result.download} Mbps / 上行 ${result.upload} Mbps)`;
                    } else if (result.error) {
                        text += ` (${result.error})`;
                    }
                } else if (t.id === 'ping') {
                    text += ` (${result})`;
                }
                setStatus(statusId, text);
            } catch (err) {
                setStatus(statusId, t.label + '：失败');
            }
            loadingOverlay.update(i + 1, tests.length);
        }

        loadingOverlay.done();
        window.location.href = '/vps';
    }

    window.addEventListener('DOMContentLoaded', run);
})();
