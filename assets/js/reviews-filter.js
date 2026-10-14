/*
  Reviews page — Client Assay Report (rating filter + summary).

  Reads the actual review cards in #reviewGrid (their data-tier attributes)
  and (re)builds the summary panel's total count, per-tier bar lengths and
  counts from them — so adding, removing or re-rating a review updates the
  Client Assay Report automatically. Nothing in that panel needs hand-editing
  when the reviews change; the HTML's own numbers are just a static fallback
  shown if this script doesn't run.

  Also wires up the rating filter: clicking a tier pill or an assay bar shows
  only reviews of that rating and hides the rest, and both the pills and the
  bars stay in sync with whichever tier is currently active.

  And animates the bars: the first time the panel scrolls into view, each
  bar grows from empty to its real width, staggered tier by tier (same
  opt-in .js-anim/.in-view pattern as the Gold Journey staircase — see
  assets/css/style.css). Only added once IntersectionObserver is confirmed
  available, so a browser without it just keeps the bars at their correct
  final width instead of being stuck at zero.
*/
(function () {
  var grid = document.getElementById("reviewGrid");
  var assay = document.getElementById("reviewAssay");
  if (!grid || !assay) return;

  var TIERS = ["24", "22", "18", "14", "9"];
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card.testimonial[data-tier]"));

  function computeCounts() {
    var counts = {};
    TIERS.forEach(function (t) { counts[t] = 0; });
    cards.forEach(function (card) {
      var t = card.getAttribute("data-tier");
      if (counts.hasOwnProperty(t)) counts[t]++;
    });
    return counts;
  }

  function renderAssay() {
    var counts = computeCounts();
    var total = cards.length;
    var max = Math.max.apply(null, TIERS.map(function (t) { return counts[t]; }).concat([1]));

    var totalEl = document.getElementById("assayTotal");
    if (totalEl) totalEl.textContent = total;
    var totalSpan = document.getElementById("filterTotal");
    if (totalSpan) totalSpan.textContent = total;

    TIERS.forEach(function (t) {
      var bar = assay.querySelector('.assay-bar[data-tier="' + t + '"]');
      if (!bar) return;
      var count = counts[t];
      var track = bar.querySelector(".assay-bar-track i");
      var countEl = bar.querySelector(".assay-bar-count");
      var widthPct = count === 0 ? 0 : Math.max(6, Math.round((count / max) * 100));
      if (track) track.style.setProperty("--w", widthPct + "%");
      if (countEl) countEl.textContent = count;
    });
  }

  function applyFilter(tier) {
    document.querySelectorAll(".pill[data-tier], .assay-bar[data-tier]").forEach(function (btn) {
      var active = btn.getAttribute("data-tier") === tier;
      if (btn.classList.contains("pill")) btn.setAttribute("aria-pressed", active ? "true" : "false");
      if (btn.classList.contains("assay-bar")) btn.setAttribute("data-active", active ? "true" : "false");
    });

    var shown = 0;
    cards.forEach(function (card) {
      var match = tier === "all" || card.getAttribute("data-tier") === tier;
      card.hidden = !match;
      if (match) shown++;
    });

    var statusEl = document.getElementById("filterStatus");
    if (!statusEl) return;
    if (tier === "all") {
      statusEl.hidden = true;
    } else {
      statusEl.hidden = false;
      var countEl = document.getElementById("filterCount");
      if (countEl) countEl.textContent = shown;
    }
  }

  document.querySelectorAll(".pill[data-tier], .assay-bar[data-tier]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyFilter(btn.getAttribute("data-tier"));
    });
  });

  var clearBtn = document.getElementById("clearFilter");
  if (clearBtn) clearBtn.addEventListener("click", function () { applyFilter("all"); });

  function initBarAnimation() {
    var barsWrap = document.getElementById("assayBars");
    if (!barsWrap || !("IntersectionObserver" in window)) return;
    // Reduced motion: never opt into .js-anim at all, so the bars stay at
    // their real, correct widths the whole time (the base CSS rule,
    // .assay-bar-track i { width: var(--w) }, is what .js-anim's
    // width:0 state temporarily overrides — skipping .js-anim means that
    // override, and the grow-in transition gated behind .in-view, never
    // applies). This replaces an earlier reduced-motion CSS rule that
    // looked right but wasn't: it tried to zero out the transition on
    // .assay-bars.js-anim .assay-bar-track i, but the .in-view variant of
    // that same selector is more specific and always won the cascade
    // regardless of the media query, so the bars still animated under
    // reduced motion. Gating .js-anim itself, here, sidesteps that
    // specificity problem entirely instead of trying to out-specificity it.
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    barsWrap.classList.add("js-anim");
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          barsWrap.classList.add("in-view");
          observer.unobserve(barsWrap);
        });
      },
      { threshold: 0.35 }
    );
    observer.observe(barsWrap);
  }

  renderAssay(); // sets each bar's real --w (and the total) before any animation class is added
  applyFilter("all");
  initBarAnimation();
})();
