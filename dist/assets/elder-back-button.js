(function () {
  "use strict";

  function isElder() {
    var root = document.querySelector("#app-root");
    return !!root && root.className.indexOf("bg-[#FFF8DC]") !== -1;
  }

  function cleanText(node) {
    return (node && node.textContent ? node.textContent : "")
      .replace(/[\s\u200B\u200C\u200D\uFEFF\u00A0]/g, "");
  }

  function findHome() {
    var items = document.querySelectorAll("nav button, nav a, .w-72 button, .w-72 a, aside button, aside a");
    for (var i = 0; i < items.length; i++) {
      if (cleanText(items[i]) === "\u9996\u9875") return items[i];
    }
    return null;
  }

  function addBack() {
    if (!isElder()) return;
    var headers = document.querySelectorAll("header");
    for (var h = 0; h < headers.length; h++) {
      var header = headers[h];
      if (header.querySelector("[data-elder-back]")) continue;
      if (cleanText(header).indexOf("\u9000\u51fa") === -1) continue;

      var btn = document.createElement("button");
      btn.setAttribute("data-elder-back", "1");
      btn.className = "memoir-back-button";
      btn.type = "button";
      btn.textContent = "\u2039 \u8fd4\u56de";
      btn.addEventListener("click", function () {
        var home = findHome();
        if (home) home.click();
        else if (window.history.length > 1) window.history.back();
      });
      header.insertBefore(btn, header.firstChild);
    }
  }

  function markBackButtons() {
    var cands = document.querySelectorAll("header button");
    for (var i = 0; i < cands.length; i++) {
      var text = cleanText(cands[i]);
      if (text === "\u9000\u56de" || text === "\u8fd4\u56de" || text === "\u2039\u8fd4\u56de" || text === "\u2039\u9000\u56de") {
        cands[i].classList.add("memoir-back-button");
        cands[i].setAttribute("data-back-fixed", "1");
      }
    }
  }

  function run() {
    addBack();
    markBackButtons();
  }

  run();
  if (window.MutationObserver) {
    var obs = new MutationObserver(run);
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  setInterval(run, 2000);
})();


