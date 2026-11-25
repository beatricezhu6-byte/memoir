(() => {
  "use strict";

  const elderLabel = "\u6211\u662f\u8001\u4eba";
  const childLabel = "\u6211\u662f\u5b50\u5973";

  function markLanding() {
    const root = document.querySelector("#root");
    if (!root) return;

    const roles = Array.from(root.querySelectorAll("button")).filter((button) => {
      const text = button.innerText || "";
      return text.includes(elderLabel) || text.includes(childLabel);
    });
    if (roles.length !== 2) return;

    const page = roles[0].closest("main")?.parentElement;
    if (!page || page.dataset.gentleRevealApplied) return;

    const title = page.querySelector("h1");
    if (!title) return;

    page.dataset.gentleRevealApplied = "true";
    page.classList.add("gentle-reveal-landing");
    roles.forEach((button, index) => {
      button.classList.add("gentle-reveal-role", `gentle-reveal-role-${index + 1}`);
    });

    const copy = Array.from(page.querySelectorAll("p"))
      .find((node) => !roles.some((button) => button.contains(node)));
    if (copy) copy.classList.add("gentle-reveal-copy");

    requestAnimationFrame(() => requestAnimationFrame(() => {
      page.classList.add("gentle-reveal-ready");
    }));
  }

  window.addEventListener("load", () => {
    markLanding();
    const root = document.querySelector("#root");
    if (root) new MutationObserver(markLanding).observe(root, { childList: true, subtree: true });
  });
})();


