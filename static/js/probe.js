(function(){
    async function run() {
        const tests = [
            async () => {
                const res = await fetch('/ping/1.1.1.1');
                return await res.text();
            },
            async () => {
                const res = await fetch('/traceroute/1.1.1.1');
                return await res.text();
            }
        ];

        loadingOverlay.start('运行网络测试');

        for (let i = 0; i < tests.length; i++) {
            const test = tests[i];
            try {
                await test();
            } catch (err) {
                // ignore errors
            }
            loadingOverlay.update(i + 1, tests.length);
        }

        loadingOverlay.done();
        window.location.href = '/vps';
    }

    window.addEventListener('DOMContentLoaded', run);
})();
