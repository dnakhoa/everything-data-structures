// Expand every hint and solution when the book is printed or saved as PDF,
// then restore the reader's open/closed state afterwards.
(function () {
  var opened = [];
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details:not([open])").forEach(function (d) {
      d.open = true;
      opened.push(d);
    });
  });
  window.addEventListener("afterprint", function () {
    opened.forEach(function (d) { d.open = false; });
    opened = [];
  });
})();
