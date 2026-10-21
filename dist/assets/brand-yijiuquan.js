/* Visible branding only. Existing routes, API names, and click handlers are untouched. */
(function () {
  var replacement = "忆旧泉";
  var pending = false;

  function replaceText(value) {
    return value && value.indexOf("回忆录") !== -1 ? value.replaceAll("回忆录", replacement) : value;
  }

  function updateBranding() {
    pending = false;
    var root = document.getElementById("root") || document.body;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      var parent = node.parentElement;
      if (!parent || /^(SCRIPT|STYLE|NOSCRIPT)$/i.test(parent.tagName)) continue;
      var nextText = replaceText(node.nodeValue);
      if (nextText !== node.nodeValue) node.nodeValue = nextText;
    }

    root.querySelectorAll("[placeholder], [title], [aria-label], [alt]").forEach(function (element) {
      ["placeholder", "title", "aria-label", "alt"].forEach(function (attribute) {
        var current = element.getAttribute(attribute);
        var next = replaceText(current);
        if (next !== current) element.setAttribute(attribute, next);
      });
    });

    document.title = replaceText(document.title);
  }

  function scheduleBranding() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(updateBranding);
  }

  window.addEventListener("load", scheduleBranding);
  new MutationObserver(scheduleBranding).observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}());
