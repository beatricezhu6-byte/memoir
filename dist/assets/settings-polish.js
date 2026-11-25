(() => {
  "use strict";

  const SAVE_TEXT = "\u4fdd\u5b58\u8bbe\u7f6e";
  const SETTINGS_TITLE = "\u4e2a\u4eba\u8bbe\u7f6e";
  const NAME_PLACEHOLDER = "\u674e\u5976\u5976";

  const getSettingsPage = () => Array.from(document.querySelectorAll("div")).find((page) => {
    const main = Array.from(page.children).find((child) => child.tagName === "MAIN");
    const header = Array.from(page.children).find((child) => child.tagName === "HEADER");
    if (!main || !header) return false;
    const hasTitle = header.querySelector("h2")?.textContent?.includes(SETTINGS_TITLE);
    const hasNameField = Array.from(main.querySelectorAll("input")).some((field) =>
      field.placeholder.includes(NAME_PLACEHOLDER)
    );
    const hasSaveButton = Array.from(main.querySelectorAll("button")).some((button) =>
      button.textContent.includes(SAVE_TEXT)
    );
    return hasTitle && hasNameField && hasSaveButton;
  });

  const clearOtherPages = (current) => {
    document.querySelectorAll(".memoir-settings-polish").forEach((page) => {
      if (page !== current) page.classList.remove("memoir-settings-polish");
    });
  };

  const decorate = () => {
    const page = getSettingsPage();
    clearOtherPages(page);
    if (!page) return;

    page.classList.add("memoir-settings-polish");
    const panel = page.querySelector(":scope > main > div");
    if (!panel || panel.querySelector("[data-settings-welcome]")) return;

    const welcome = document.createElement("section");
    welcome.className = "settings-welcome";
    welcome.dataset.settingsWelcome = "true";
    welcome.innerHTML = [
      '<span class="settings-welcome-icon" aria-hidden="true"></span>',
      '<div><h3>\u5b8c\u5584\u4e2a\u4eba\u4fe1\u606f</h3><p>\u586b\u5199\u60a8\u7684\u4fe1\u606f\uff0c\u8ba9\u56de\u5fc6\u8bb0\u5f55\u66f4\u52a0\u5b8c\u6574~</p></div>',
      '<span class="settings-welcome-note">\u8ba4\u771f\u751f\u6d3b<br>\u6536\u85cf\u6bcf\u4e00\u4e2a\u503c\u5f97\u7eaa\u5ff5\u7684\u77ac\u95f4</span>'
    ].join("");
    panel.prepend(welcome);

    const note = document.createElement("p");
    note.className = "settings-privacy-note";
    note.textContent = "\u60a8\u7684\u4fe1\u606f\u4ec5\u7528\u4e8e\u4e2a\u6027\u5316\u4f53\u9a8c\uff0c\u6211\u4eec\u4f1a\u59a5\u5584\u4fdd\u62a4\u60a8\u7684\u9690\u79c1\u5b89\u5168\u3002";
    panel.append(note);
  };

  const initialize = () => {
    decorate();
    new MutationObserver(decorate).observe(document.body, { childList: true, subtree: true });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();


