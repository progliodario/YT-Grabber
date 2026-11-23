/* The language of the user is loaded now, before the page is shown, so that a screen reader never reads the English texts first.
   It runs after lang/en.js and before app.js (index.html), and only knows the first language of the browser: app.js decides the rest. */
(function () {
  var l = null, a;
  try { l = localStorage.getItem('ytg-lang'); } catch (e) { l = null; }
  if (!l) { a = (navigator.languages && navigator.languages[0]) || navigator.language || 'en'; l = String(a).toLowerCase().split('-')[0]; if (l === 'in') { l = 'id'; } }
  if (/^(it|es|fr|de|pt|nl|pl|ru|tr|ar|hi|id|zh|ja|ko)$/.test(l)) { document.write('<script src="lang/' + l + '.js"><\/script>'); }
}());
