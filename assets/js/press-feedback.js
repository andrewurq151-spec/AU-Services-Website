/*
  iOS Safari gotcha: the :active CSS pseudo-class is only honored on an
  element if the page has *some* touchstart listener registered somewhere
  (even a no-op one) — otherwise Safari skips :active entirely on tap and
  jumps straight to whatever the tap triggers (a click, a navigation),
  so a button/link/card never visibly shows its press state at all on
  iPhone/iPad. This is the standard, documented fix: one empty, passive
  listener, loaded on every page, enables :active site-wide (buttons,
  nav links, footer links, the homepage service cards — see their
  :active rules in assets/css/style.css).
*/
document.addEventListener("touchstart", function () {}, { passive: true });
