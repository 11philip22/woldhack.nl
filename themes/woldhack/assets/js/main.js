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

  function initClickableCards() {
    var cards = document.querySelectorAll(".content-card[data-card-href]");
    if (!cards.length) {
      return;
    }

    var interactiveSelector = "a, button, input, textarea, select, label, summary, [role='button']";

    var navigate = function (card) {
      var href = card.getAttribute("data-card-href");
      if (href) {
        window.location.href = href;
      }
    };

    cards.forEach(function (card) {
      card.addEventListener("click", function (event) {
        if (event.defaultPrevented || event.button !== 0) {
          return;
        }

        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
          return;
        }

        if (event.target && event.target.closest(interactiveSelector)) {
          return;
        }

        navigate(card);
      });

      card.addEventListener("keydown", function (event) {
        if (event.defaultPrevented || (event.key !== "Enter" && event.key !== " ")) {
          return;
        }

        if (event.target && event.target !== card && event.target.closest(interactiveSelector)) {
          return;
        }

        event.preventDefault();
        navigate(card);
      });
    });
  }

  function init() {
    initThemeToggle();
    initClickableCards();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
