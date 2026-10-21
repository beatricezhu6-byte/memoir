(function () {
  var appliedAt = 0;

  function isChildRoot() {
    var root = document.querySelector("#app-root");
    return !!root && String(root.className || "").indexOf("bg-slate-900") !== -1;
  }

  function findDrawer() {
    return document.querySelector("div.fixed.top-0.left-0.h-full.w-72");
  }

  function normalizedText(node) {
    return (node && node.textContent ? node.textContent : "").replace(/\s+/g, "");
  }

  function clickButtonByText(texts, scope, ignoredButton) {
    var buttons = Array.prototype.slice.call(document.querySelectorAll("button"));
    for (var i = 0; i < buttons.length; i += 1) {
      var button = buttons[i];
      if (button === ignoredButton) continue;
      if (scope && !scope.contains(button)) continue;
      var label = normalizedText(button);
      for (var j = 0; j < texts.length; j += 1) {
        if (label === texts[j] || label.indexOf(texts[j]) !== -1) {
          button.click();
          return true;
        }
      }
    }
    return false;
  }

  function makeButton(label, type, drawer) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "memoir-drawer-action memoir-drawer-action-" + type;
    button.textContent = label;
    button.addEventListener("click", function () {
      if (type === "switch") {
        if (clickButtonByText(["\u5207\u6362\u8eab\u4efd", "\u9000\u51fa"], null, button)) return;
        window.location.href = window.location.pathname;
        return;
      }
      if (clickButtonByText(["\u9996\u9875"], drawer, button)) return;
      var closeButton = drawer.querySelector(".memoir-drawer-head button");
      if (closeButton) closeButton.click();
    });
    return button;
  }

  function buildProfile(child) {
    var profile = document.createElement("div");
    var title = document.createElement("strong");
    var subtitle = document.createElement("span");
    var avatar = document.createElement("div");
    var text = document.createElement("div");

    profile.className = "memoir-drawer-profile";
    avatar.className = "memoir-drawer-avatar";
    avatar.setAttribute("aria-hidden", "true");
    title.textContent = "\u6b22\u8fce\u56de\u6765";
    subtitle.textContent = child
      ? "\u966a\u4f34\u8bb0\u5f55 \u00b7 \u73cd\u85cf\u65f6\u5149"
      : "\u8bb0\u5f55\u751f\u6d3b \u00b7 \u73cd\u85cf\u65f6\u5149";

    text.appendChild(title);
    text.appendChild(subtitle);
    profile.appendChild(avatar);
    profile.appendChild(text);
    return profile;
  }

  function applyDrawer() {
    var now = Date.now();
    if (now - appliedAt < 40) return;
    appliedAt = now;

    var drawer = findDrawer();
    if (!drawer) return;

    var child = isChildRoot();
    drawer.classList.add("memoir-drawer-polished");
    drawer.classList.toggle("memoir-drawer-child", child);
    drawer.classList.toggle("memoir-drawer-elder", !child);

    var header = drawer.children[0];
    var nav = drawer.querySelector("nav");
    if (header) header.classList.add("memoir-drawer-head");
    if (nav) {
      nav.classList.add("memoir-drawer-nav");
      Array.prototype.slice.call(nav.querySelectorAll("button")).forEach(function (button) {
        button.classList.add("memoir-drawer-item");
      });
    }

    if (header && !drawer.querySelector(".memoir-drawer-profile")) {
      header.insertAdjacentElement("afterend", buildProfile(child));
    }

    if (!drawer.querySelector(".memoir-drawer-footer")) {
      var footer = document.createElement("div");
      footer.className = "memoir-drawer-footer";
      footer.appendChild(makeButton("\u5207\u6362\u8eab\u4efd", "switch", drawer));
      footer.appendChild(makeButton("\u8fd4\u56de\u9996\u9875", "home", drawer));
      drawer.appendChild(footer);
    }
  }

  function scheduleApply() {
    if (scheduleApply.pending) return;
    scheduleApply.pending = true;
    window.requestAnimationFrame(function () {
      scheduleApply.pending = false;
      applyDrawer();
    });
  }

  applyDrawer();
  document.addEventListener("click", function () {
    window.setTimeout(applyDrawer, 80);
  }, true);
  new MutationObserver(scheduleApply).observe(document.body, {
    childList: true,
    subtree: true
  });
})();
