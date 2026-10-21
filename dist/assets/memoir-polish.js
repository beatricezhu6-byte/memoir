window.addEventListener("load", () => {
  document.title = "回忆录助手";

  const markLanding = () => {
    document.querySelectorAll("#app-root > div > div > div.relative.z-10").forEach((section) => {
      if (section.querySelector("h1") && section.querySelector("button.flex-1")) {
        section.classList.add("memoir-landing");
      }
    });

    document.querySelectorAll("#app-root > div > div").forEach((page) => {
      const actionRow = page.querySelector(":scope > main > div > div.flex.items-center.justify-center.gap-4");
      if (actionRow && actionRow.querySelectorAll("button").length === 2) {
        page.classList.add("memoir-timeline");
        const panel = actionRow.parentElement;
        if (panel && !panel.querySelector(".timeline-decoration")) {
          const decoration = document.createElement("div");
          decoration.className = "timeline-decoration";

          const preview = document.createElement("div");
          preview.className = "timeline-preview-copy";
          preview.innerHTML = "<strong>人生阶段预览</strong><span>从童年到奋斗，把每段故事串联起来</span>";

          const memories = ["童年时光", "求学岁月", "组建家庭", "奋斗岁月"];
          memories.forEach((label, index) => {
            const card = document.createElement("div");
            card.className = "timeline-memory-card";
            card.innerHTML = `<span class="timeline-photo" aria-hidden="true"></span><span class="timeline-caption">${label}</span>`;
            if (index === 2) {
              decoration.appendChild(createTimelineNotebook());
            }
            decoration.appendChild(card);
          });
          actionRow.insertAdjacentElement("afterend", preview);
          preview.insertAdjacentElement("afterend", decoration);

          const note = document.createElement("div");
          note.className = "timeline-note";
          note.innerHTML = "<strong>点击上方按钮生成您的人生大事年表</strong><span>让珍贵的回忆，按时间串联成一段美好的人生旅程。</span>";
          decoration.insertAdjacentElement("afterend", note);
        }
      }

    });
  };

  markLanding();
  const root = document.querySelector("#root");
  if (root) {
    new MutationObserver(markLanding).observe(root, {
      childList: true,
      subtree: true,
    });
  }
});

function createTimelineNotebook() {
  const notebook = document.createElement("div");
  notebook.className = "timeline-notebook";
  notebook.textContent = "人生大事年表";
  return notebook;
}
