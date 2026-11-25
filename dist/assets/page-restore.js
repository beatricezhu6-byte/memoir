(() => {
  "use strict";

  const keys = {
    page: "memoir-current-page",
    role: "memoir-current-role"
  };

  const labels = {
    elder: "\u6211\u662f\u8001\u4eba",
    child: "\u6211\u662f\u5b50\u5973",
    start: "\u5f00\u542f\u6211\u7684\u56de\u5fc6\u5f55\u4e4b\u65c5",
    timeline: "\u5927\u4e8b\u5e74\u8868",
    chat: "\u804a\u5929\u5f15\u5bfc",
    memoir: "\u6211\u7684\u56de\u5fc6\u5f55",
    record: "\u5f55\u5236\u60a8\u7684\u56de\u5fc6",
    settings: "\u4e2a\u4eba\u8bbe\u7f6e",
    platform: "\u5b9a\u5236\u5e73\u53f0"
  };

  let restoring = false;
  let restoreAttempts = 0;

  const buttonWith = (text) => Array.from(document.querySelectorAll("button"))
    .find((button) => button.innerText && button.innerText.includes(text));

  const pageFromScreen = () => {
    const heading = Array.from(document.querySelectorAll("h2"))
      .map((node) => node.textContent.trim())
      .find(Boolean);
    if (!heading) return "";
    if (heading.includes(labels.timeline)) return "timeline";
    if (heading.includes(labels.chat)) return "chat";
    if (heading.includes(labels.memoir)) return "memoir";
    if (heading.includes(labels.record)) return "record";
    if (heading.includes(labels.settings)) return "settings";
    if (heading.includes(labels.platform)) return "platform";
    return "";
  };

  const rememberScreen = () => {
    if (restoring) return;
    const page = pageFromScreen();
    if (page) sessionStorage.setItem(keys.page, page);
  };

  const restoreScreen = () => {
    const target = sessionStorage.getItem(keys.page);
    if (!target || restoreAttempts++ > 16) {
      restoring = false;
      return;
    }

    const current = pageFromScreen();
    if (current === target) {
      restoring = false;
      return;
    }

    restoring = true;
    const role = sessionStorage.getItem(keys.role) || "elder";
    const identityButton = buttonWith(role === "child" ? labels.child : labels.elder);
    if (identityButton) {
      identityButton.click();
      return;
    }

    const startButton = buttonWith(labels.start);
    if (startButton) {
      startButton.click();
      return;
    }

    const targetLabel = labels[target];
    const targetButton = targetLabel && buttonWith(targetLabel);
    if (targetButton) {
      targetButton.click();
      return;
    }
  };

  window.addEventListener("load", () => {
    document.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const text = button.innerText || "";
      if (text.includes(labels.elder)) sessionStorage.setItem(keys.role, "elder");
      if (text.includes(labels.child)) sessionStorage.setItem(keys.role, "child");
      window.setTimeout(rememberScreen, 120);
    }, true);

    const root = document.querySelector("#root");
    if (root) new MutationObserver(rememberScreen).observe(root, { childList: true, subtree: true });

    // Do not replay a saved route while the visitor is already choosing a page.
    // It used to click through the child portal again during a normal transition,
    // which could interrupt the timeline and leave the screen blank.
    const restoreRequested = new URLSearchParams(window.location.search).get("restore") === "1";
    if (restoreRequested) {
      window.setTimeout(() => {
        if (sessionStorage.getItem(keys.page)) restoreScreen();
      }, 700);
      window.setInterval(() => {
        if (restoring) restoreScreen();
      }, 240);
    }
  });
})();


