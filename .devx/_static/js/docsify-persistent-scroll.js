(function () {
    'use strict';

    function persistentScroll(hook, vm) {
        const positions = new Map();
        let key = location.pathname + vm.route.path;
        let rendering = false;

        window.addEventListener('scroll', () => {
            if (!rendering) positions.set(key, window.scrollY);
        }, { passive: true });

        hook.beforeEach(content => {
            rendering = true;
            key = location.pathname + vm.route.path;
            return content;
        });
        hook.doneEach(() => {
            requestAnimationFrame(() => {
                // Let Docsify handle explicit anchors. Restore a route only once.
                if (!vm.route.query?.id) window.scrollTo(0, positions.get(key) || 0);
                rendering = false;
            });
        });
    }

    window.$docsify = window.$docsify || {};
    window.$docsify.plugins = (window.$docsify.plugins || []).concat(persistentScroll);
})();
