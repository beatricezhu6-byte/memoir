(() => {
  const cardSelector =
    '#app-root > div > div:has(> header + main > div > div.grid > button h4) main div.grid > button';

  function addChatLabels() {
    document.querySelectorAll(cardSelector).forEach((card, index) => {
      if (index > 5) return;
      if (card.querySelector(':scope > .memoir-chat-cta')) return;

      const label = document.createElement('span');
      label.className = 'memoir-chat-cta';
      label.setAttribute('aria-hidden', 'true');
      label.append(document.createTextNode('和TA聊天 '));

      const arrow = document.createElement('span');
      arrow.className = 'memoir-chat-arrow';
      arrow.textContent = '→';
      label.append(arrow);
      card.append(label);
    });
  }

  addChatLabels();
  new MutationObserver(addChatLabels).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();


