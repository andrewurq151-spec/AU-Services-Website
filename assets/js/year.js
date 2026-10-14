/*
  Keeps the footer copyright year current automatically, so it never goes
  stale again. The HTML already contains a correct, real year as static
  text (see #copyright-year in each footer) — this just swaps it for
  whatever the visitor's own clock says the year is, when JS is available.
*/
(function () {
  var el = document.getElementById("copyright-year");
  if (!el) return;
  var y = new Date().getFullYear();
  if (y && y > 2000) {
    el.textContent = y;
  }
})();
