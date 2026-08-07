
/*
 * Minimal hand-written Module Federation container for a JupyterLab prebuilt
 * extension. Exposes the JupyterLab `app` object as `window.jupyterapp` so the
 * DevX workshop lesson iframes (which call window.parent.jupyterapp) work
 * without the NVIDIA AI Workbench DevX injection layer.
 *
 * JupyterLab federated loader protocol:
 *   window._JUPYTERLAB[<name>] = { init(shareScope), get(module) }
 *   get('./extension') -> Promise<factory>, factory() -> module namespace
 *   The module's `default` export is a JupyterLab plugin object.
 */
var _JUPYTERLAB = (typeof window !== "undefined" && window._JUPYTERLAB) || {};
if (typeof window !== "undefined") { window._JUPYTERLAB = _JUPYTERLAB; }

(function () {
  "use strict";

  // The plugin: autoStart, requires nothing, assigns app to window.
  var plugin = {
    id: "devx-jupyterapp-bridge:plugin",
    autoStart: true,
    activate: function (app) {
      try {
        window.jupyterapp = app;
        // Some DevX code also checks window.parent from an iframe; top window is this one.
        console.log("[devx-jupyterapp-bridge] window.jupyterapp is now available.");
      } catch (e) {
        console.error("[devx-jupyterapp-bridge] failed to expose app:", e);
      }
    }
  };

  // The module namespace returned for './extension' and './index'.
  var extensionModule = { default: plugin, __esModule: true };

  var factories = {
    "./extension": function () { return Promise.resolve(function () { return extensionModule; }); },
    "./index": function () { return Promise.resolve(function () { return extensionModule; }); }
  };

  _JUPYTERLAB["devx-jupyterapp-bridge"] = {
    init: function (shareScope) {
      // No shared modules needed; accept and ignore the share scope.
      return Promise.resolve();
    },
    get: function (moduleName) {
      var f = factories[moduleName];
      if (f) { return f(); }
      return Promise.reject(new Error('Module "' + moduleName + '" does not exist in container.'));
    }
  };
})();
