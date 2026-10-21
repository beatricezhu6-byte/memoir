/* Keep the child portal timeline independent from the approved elder timeline.
   This observer is intentionally idempotent: writing the same text on every
   mutation used to trigger itself repeatedly and could freeze the route. */
(function () {
  var polished = "data-child-timeline-polished";

  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }

  function markChildTimeline() {
    document.querySelectorAll("#app-root > div > div").forEach(function (page) {
      var row = page.querySelector(":scope > main > div > div.flex.items-center.justify-center.gap-4");
      var isChildPortal = page.classList.contains("from-slate-900");
      if (!row || row.querySelectorAll("button").length !== 2 || !isChildPortal) return;

      page.classList.add("memoir-child-timeline");
      if (page.hasAttribute(polished)) return;
      page.setAttribute(polished, "true");

      var preview = page.querySelector(".timeline-preview-copy");
      if (preview) {
        setText(preview.querySelector("strong"), "\u966a\u4f34\u6574\u7406 \u00b7 \u4eba\u751f\u9636\u6bb5\u9884\u89c8");
        setText(preview.querySelector("span"), "\u548c\u7236\u6bcd\u4e00\u8d77\uff0c\u628a\u73cd\u8d35\u6545\u4e8b\u6162\u6162\u4e32\u8054\u8d77\u6765");
      }

      var note = page.querySelector(".timeline-note");
      if (note) {
        setText(note.querySelector("strong"), "\u70b9\u51fb\u4e0a\u65b9\u6309\u94ae\uff0c\u5e2e\u7236\u6bcd\u6574\u7406\u4eba\u751f\u5927\u4e8b\u5e74\u8868");
        setText(note.querySelector("span"), "\u6bcf\u4e00\u4e2a\u65f6\u95f4\u8282\u70b9\uff0c\u90fd\u662f\u5bb6\u4eba\u5171\u540c\u73cd\u85cf\u7684\u8bb0\u5fc6\u3002");
      }
    });
  }

  window.addEventListener("load", markChildTimeline);
  new MutationObserver(markChildTimeline).observe(document.documentElement, { childList: true, subtree: true });
}());
