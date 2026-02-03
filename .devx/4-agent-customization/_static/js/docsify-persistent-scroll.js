(function () {
    /**
     * docsify-persistent-scroll.js
     *
     * This plugin watches for unexpected scroll resets caused by environments like JupyterLab,
     * where iframe tabs may be dynamically attached/detached from the DOM without triggering
     * standard visibility, load, or focus events. This breaks normal scroll persistence.
     *
     * To work around this:
     * - The plugin tracks scroll position in memory (not persisted).
     * - It does NOT restore scroll position on the first page load (avoiding jumpy behavior).
     * - It starts polling after first load and only restores scroll if it detects the scroll
     *   position has unexpectedly reset (e.g., from tab switching in JupyterLab).
     */

    function docsifyPersistentScrollPlugin(hook, vm) {
        const scrollMemory = {};
        let restoreScrollPosition = false;
        const key = `${location.pathname}${location.hash}`;
        let hasInitialLoadRun = false;
        let lastScrollY = window.scrollY;

        // Track scroll changes in memory
        window.addEventListener("scroll", () => {
            let scrollY = window.scrollY;
            if (scrollY > 0) {
                scrollMemory[key] = scrollY;
                lastScrollY = scrollY;
            } else {
                restoreScrollPosition = true;
            }
        });

        // Docsify finishes rendering a page
        hook.doneEach(function () {
            hasInitialLoadRun = true;
            lastScrollY = window.scrollY;
        });

        // Poll every 50ms to detect scroll resets
        setInterval(() => {
            if (!hasInitialLoadRun) return;

            if (!restoreScrollPosition) return;

            window.scrollTo(0, scrollMemory[key]);

            if (window.scrollY > 0) {
                restoreScrollPosition = false;
                scrollMemory[key] = window.scrollY;
            }
        }, 50);
    }

    if (window.$docsify) {
        window.$docsify.plugins = (window.$docsify.plugins || []).concat(docsifyPersistentScrollPlugin);
    } else {
        window.$docsify = {
            plugins: [docsifyPersistentScrollPlugin]
        };
    }
})();
