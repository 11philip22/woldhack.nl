(function () {
  var storageKey = "woldhack-theme-mode";

  function noise(x, y) {
    return (
      Math.sin(x * 0.8 + y * 1.3) * 0.4 +
      Math.sin(x * 1.7 - y * 0.6 + 2.1) * 0.25 +
      Math.sin(x * 0.4 + y * 2.1 + 4.3) * 0.2 +
      Math.cos(x * 2.3 + y * 0.9 + 1.1) * 0.15
    );
  }

  function createVoidSeed() {
    return {
      voidOffsetA: Math.random() * 1800,
      voidOffsetB: Math.random() * 1800,
      voidOffsetC: Math.random() * 1800,
      voidOffsetD: Math.random() * 1800,
      voidWarpPrimaryX: 68 + Math.random() * 40,
      voidWarpSecondaryX: 24 + Math.random() * 26,
      voidWarpPrimaryY: 70 + Math.random() * 42,
      voidWarpSecondaryY: 24 + Math.random() * 26,
      voidLevels: 14 + Math.floor(Math.random() * 6),
      voidLevelSpread: 1.3 + Math.random() * 0.45,
      voidLineBoost: 0.88 + Math.random() * 0.32,
    };
  }

  function sampleVoidField(x, y, seed) {
    var warpX =
      noise((x + seed.voidOffsetA) * 0.006 + 4.1, (y - seed.voidOffsetB) * 0.006 - 1.9) * seed.voidWarpPrimaryX +
      noise((x - seed.voidOffsetC) * 0.014 - 3.2, (y + seed.voidOffsetD) * 0.01 + 2.7) * seed.voidWarpSecondaryX;
    var warpY =
      noise((x - seed.voidOffsetD) * 0.006 - 2.6, (y + seed.voidOffsetA) * 0.006 + 3.4) * seed.voidWarpPrimaryY +
      noise((x + seed.voidOffsetB) * 0.012 + 1.8, (y - seed.voidOffsetC) * 0.012 - 4.3) * seed.voidWarpSecondaryY;
    var wx = x + warpX;
    var wy = y + warpY;

    var base =
      noise(wx * 0.013, wy * 0.028) * 0.84 +
      noise(wx * 0.039 + 7.3, wy * 0.021 + 11.6) * 0.44 +
      noise((wx + wy * 0.33) * 0.018, (wy - wx * 0.27) * 0.02) * 0.31;

    var flow =
      Math.sin(wx * 0.018 + wy * 0.01 + noise(x * 0.012, y * 0.012) * 2.1) * 0.18 +
      Math.cos(wx * 0.01 - wy * 0.019 + noise(x * 0.017 + 2.4, y * 0.015 - 1.7) * 1.7) * 0.13;

    return (base + flow) * 0.78;
  }

  function edgePoint(x, y, step, edge, v00, v10, v11, v01, level) {
    if (edge === 0) {
      var dt = v10 - v00 || 1e-6;
      return [x + step * ((level - v00) / dt), y];
    }
    if (edge === 1) {
      var dr = v11 - v10 || 1e-6;
      return [x + step, y + step * ((level - v10) / dr)];
    }
    if (edge === 2) {
      var db = v11 - v01 || 1e-6;
      return [x + step * ((level - v01) / db), y + step];
    }
    var dl = v01 - v00 || 1e-6;
    return [x, y + step * ((level - v00) / dl)];
  }

  function drawVoid(ctx, width, height, isLight, seed) {
    var step = 5;
    var cols = Math.ceil(width / step);
    var rows = Math.ceil(height / step);
    var field = new Array(rows + 1);
    var gy;
    var gx;

    for (gy = 0; gy <= rows; gy++) {
      field[gy] = new Float32Array(cols + 1);
      for (gx = 0; gx <= cols; gx++) {
        field[gy][gx] = sampleVoidField(gx * step, gy * step, seed);
      }
    }

    var segmentsByCase = {
      1: [[3, 0]],
      2: [[0, 1]],
      3: [[3, 1]],
      4: [[1, 2]],
      5: [[0, 1], [3, 2]],
      6: [[0, 2]],
      7: [[3, 2]],
      8: [[2, 3]],
      9: [[0, 2]],
      10: [[0, 3], [1, 2]],
      11: [[1, 2]],
      12: [[1, 3]],
      13: [[0, 1]],
      14: [[0, 3]],
    };

    var levels = seed.voidLevels;
    var minLevel = -seed.voidLevelSpread;
    var maxLevel = seed.voidLevelSpread;
    var i;

    for (i = 0; i < levels; i++) {
      var t = i / Math.max(1, levels - 1);
      var level = minLevel + (maxLevel - minLevel) * t;
      var rawBrightness = 0.12 + t * 0.2;
      var brightness = isLight ? 1 - rawBrightness : rawBrightness;
      var v = Math.round(brightness * 255);
      var alpha = 0.22 + (1 - Math.abs(t - 0.5) * 1.65) * 0.36;

      ctx.strokeStyle = "rgba(" + v + "," + v + "," + v + "," + Math.max(0.08, alpha).toFixed(2) + ")";
      ctx.lineWidth = (0.9 + (1 - Math.abs(t - 0.5) * 1.4) * 0.8) * seed.voidLineBoost;
      ctx.beginPath();

      for (gy = 0; gy < rows; gy++) {
        for (gx = 0; gx < cols; gx++) {
          var v00 = field[gy][gx];
          var v10 = field[gy][gx + 1];
          var v11 = field[gy + 1][gx + 1];
          var v01 = field[gy + 1][gx];

          var c0 = v00 >= level ? 1 : 0;
          var c1 = v10 >= level ? 1 : 0;
          var c2 = v11 >= level ? 1 : 0;
          var c3 = v01 >= level ? 1 : 0;
          var mask = c0 | (c1 << 1) | (c2 << 2) | (c3 << 3);
          var pairs = segmentsByCase[mask];
          if (!pairs) {
            continue;
          }

          var x = gx * step;
          var y = gy * step;
          var p;
          for (p = 0; p < pairs.length; p++) {
            var edges = pairs[p];
            var a = edgePoint(x, y, step, edges[0], v00, v10, v11, v01, level);
            var b = edgePoint(x, y, step, edges[1], v00, v10, v11, v01, level);
            ctx.moveTo(a[0], a[1]);
            ctx.lineTo(b[0], b[1]);
          }
        }
      }
      ctx.stroke();
    }
  }

  function renderPanelVoid(panel) {
    var rect = panel.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      return;
    }

    var canvas = panel.querySelector("\.void-bg");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.className = "void-bg";
      canvas.setAttribute("aria-hidden", "true");
      panel.insertBefore(canvas, panel.firstChild);
    }

    if (!panel._voidSeed) {
      panel._voidSeed = createVoidSeed();
    }

    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var width = Math.max(1, Math.round(rect.width));
    var height = Math.max(1, Math.round(rect.height));
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";

    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    var isLight = document.body.classList.contains("is-light");
    drawVoid(ctx, width, height, isLight, panel._voidSeed);
  }

  function initVoidPanels() {
    var panels = document.querySelectorAll(".hero-panel");
    if (!panels.length) {
      return;
    }

    var drawAll = function () {
      panels.forEach(function (panel) {
        renderPanelVoid(panel);
      });
    };

    drawAll();

    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(drawAll, 120);
    });

    document.addEventListener("woldhack-theme-change", drawAll);
  }

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
      document.dispatchEvent(new CustomEvent("woldhack-theme-change"));
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
    initVoidPanels();
    initClickableCards();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

