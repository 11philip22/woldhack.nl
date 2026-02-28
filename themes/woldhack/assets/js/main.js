(function () {
  var storageKey = "woldhack-theme-mode";

  function initThemeToggle() {
    var body = document.body;
    var toggle = document.querySelector("[data-theme-toggle]");

    if (!body || !toggle) {
      return;
    }

    var updateToggleLabel = function (mode) {
      toggle.textContent = mode === "light" ? "DARK MODE" : "LIGHT MODE";
      toggle.setAttribute("aria-label", "Switch to " + (mode === "light" ? "dark" : "light") + " mode");
    };

    var setMode = function (mode, persist) {
      var isLight = mode === "light";
      body.classList.toggle("is-light", isLight);
      updateToggleLabel(mode);
      if (persist) {
        window.localStorage.setItem(storageKey, mode);
      }
    };

    var savedMode = window.localStorage.getItem(storageKey);
    var prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    var initialMode = savedMode || (prefersLight ? "light" : "dark");

    setMode(initialMode, false);

    toggle.addEventListener("click", function () {
      var nextMode = body.classList.contains("is-light") ? "dark" : "light";
      setMode(nextMode, true);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeToggle, { once: true });
  } else {
    initThemeToggle();
  }
})();
