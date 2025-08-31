// VIBE-CODED: ChatGPT 5
/* eslint-disable @typescript-eslint/no-require-imports */
(function () {
  function hasRequire() { return typeof window.requirejs !== "undefined"; }

  function configure() {
    if (!hasRequire()) return false;

    // If you ever need explicit config again, uncomment & fill in:
    // requirejs.config({
    //   waitSeconds: 0,
    //   packages: [ /* { name, location, main } */ ],
    //   paths: { /* 'underscore': '...', etc. */ }
    // });

    // Diagnostics (keeps existing handler if there is one)
    if (typeof requirejs.onError === "function") {
      var prev = requirejs.onError;
      requirejs.onError = function (err) {
        console.error("[widgets-amd-config] RequireJS error:", err);
        try { prev(err); } catch (_) {}
      };
    }

    // Mark that a config pass happened (even if it was a no-op)
    window.__amd_config_loaded__ = true;

    // Optional: warm base right here too (safe & idempotent)
    try {
      require(['@jupyter-widgets/base'], function () {
        window.__widgets_base_ready__ = true;
      });
    } catch (_) { /* If manager isn't registered yet, warm script will handle it */ }

    return true;
  }

  if (!configure()) {
    // If this runs before require.js is present, retry briefly
    var tries = 40;
    (function tick() {
      if (configure()) return;
      if (--tries <= 0) {
        console.error("[widgets-amd-config] Gave up waiting for requirejs.");
        return;
      }
      setTimeout(tick, 50);
    })();
  }
})();