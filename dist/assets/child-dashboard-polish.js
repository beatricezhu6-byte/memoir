(function () {
  var ROOT = "memoir-child-dashboard-polish";
  var CARD_CLASS = "memoir-child-action-card";
  var TITLES = [
    "\u5f55\u5236\u56de\u5fc6",
    "\u8bbf\u8c08\u63d0\u793a",
    "\u56de\u5fc6\u5f55",
    "\u5927\u4e8b\u5e74\u8868",
    "\u4e2a\u4eba\u8bbe\u7f6e",
    "\u5b9a\u5236\u670d\u52a1"
  ];

  function textOf(node) {
    return (node && node.textContent ? node.textContent : "").replace(/\s+/g, "");
  }

  function isChildDashboard() {
    var main = document.querySelector("main");
    if (!main) return false;
    var pageText = textOf(main);
    return pageText.indexOf("\u5e2e\u7236\u6bcd\u8bb0\u5f55\u73cd\u8d35\u56de\u5fc6") !== -1 &&
      TITLES.every(function (title) { return pageText.indexOf(title) !== -1; });
  }

  function enhance() {
    document.documentElement.classList.toggle(ROOT, isChildDashboard());
    if (!document.documentElement.classList.contains(ROOT)) return;

    var buttons = Array.prototype.slice.call(document.querySelectorAll("main button"));
    buttons.forEach(function (button) {
      var titleEl = button.querySelector("h3");
      if (!titleEl) return;
      var title = textOf(titleEl);
      var index = TITLES.indexOf(title);
      if (index === -1) return;
      button.classList.add(CARD_CLASS);
      button.setAttribute("data-card-index", String(index));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhance);
  } else {
    enhance();
  }

  var observer = new MutationObserver(function () {
    window.requestAnimationFrame(enhance);
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();


