(() => {
  "use strict";

  const text = {
    preview: "\u9884\u89c8\u56de\u5fc6\u5f55",
    download: "\u4e0b\u8f7d\u56de\u5fc6\u5f55",
    sort: "AI\u667a\u80fd\u6392\u5e8f",
    record: "\u5f55\u5236\u56de\u5fc6",
    menuRecord: "\u5f55\u5236\u56de\u5fc6"
  };

  const decorateShelf = () => {
    document.querySelectorAll("#app-root > div > div").forEach((page) => {
      const buttons = Array.from(page.querySelectorAll(":scope > main button"));
      const hasShelfActions = buttons.some((button) => button.innerText.includes(text.preview))
        && buttons.some((button) => button.innerText.includes(text.download))
        && buttons.some((button) => button.innerText.includes(text.sort));
      if (!hasShelfActions) {
        page.classList.remove("memoir-shelf");
        return;
      }

      page.classList.add("memoir-shelf");
      const empty = page.querySelector(":scope > main div.flex-1.flex.flex-col");
      if (empty && !empty.querySelector("[data-memoir-empty-art]")) {
        const art = document.createElement("div");
        art.dataset.memoirEmptyArt = "true";
        art.className = "memoir-empty-art";
        art.setAttribute("aria-hidden", "true");
        empty.prepend(art);

        const action = document.createElement("button");
        action.type = "button";
        action.dataset.memoirRecordStart = "true";
        action.className = "memoir-record-start";
        action.textContent = "\u5f00\u59cb\u8bb0\u5f55\u6211\u7684\u56de\u5fc6";
        empty.append(action);
      }
    });
  };

  const initialize = () => {
    if (document.documentElement.dataset.memoirShelfReady === "true") return;
    document.documentElement.dataset.memoirShelfReady = "true";
    document.addEventListener("click", (event) => {
      const start = event.target.closest("button[data-memoir-record-start]");
      if (!start) return;
      const page = start.closest(".memoir-shelf");
      const back = page && Array.from(page.querySelectorAll("header button"))
        .find((button) => button.innerText.includes("\u9000\u56de"));
      if (!back) return;
      back.click();
      let attempts = 0;
      const openRecording = () => {
        const record = Array.from(document.querySelectorAll("button"))
          .find((button) => button.querySelector('img[alt="\u5f55\u5236\u56de\u5fc6"]'));
        if (record) {
          record.click();
          return;
        }
        if (attempts++ < 35) window.setTimeout(openRecording, 160);
      };
      window.setTimeout(openRecording, 120);
    }, true);

    decorateShelf();
    const root = document.querySelector("#root");
    if (root) new MutationObserver(decorateShelf).observe(root, { childList: true, subtree: true });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();


