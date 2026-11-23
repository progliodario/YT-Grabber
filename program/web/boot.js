/* Runs first, in the head of index.html (a separate file: the page has no inline script, so the Content-Security-Policy can forbid them). */
(function () {
  // theme chosen by the user, applied immediately to avoid a color flash
  try { var t = localStorage.getItem('ytg-theme'); if (t === 'light' || t === 'dark') { document.documentElement.setAttribute('data-theme', t); } } catch (e) { /* ignore */ }
  // text size chosen by the user (a percentage of the size set in the browser), applied at once too
  try { var z = parseInt(localStorage.getItem('ytg-textsize'), 10); if (z === 125 || z === 150 || z === 200) { document.documentElement.style.fontSize = z + '%'; } } catch (e) { /* ignore */ }
}());
