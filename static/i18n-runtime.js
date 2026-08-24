(function () {
  "use strict";
  const pairs = Array.isArray(window.PF_TRANSLATION_PAIRS) ? window.PF_TRANSLATION_PAIRS : [];
  if (!pairs.length) return;
  const map = new Map(pairs.filter(p => p && p.source && p.target).map(p => [String(p.source).trim(), String(p.target)]));
  const ignored = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "CODE", "PRE"]);
  const translate = (value) => {
    const trimmed = String(value || "").trim();
    const translated = map.get(trimmed);
    if (!translated || trimmed === translated) return value;
    const start = String(value).indexOf(trimmed);
    return start < 0 ? translated : String(value).slice(0, start) + translated + String(value).slice(start + trimmed.length);
  };
  const walk = (root) => {
    const nodes = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (nodes.nextNode()) textNodes.push(nodes.currentNode);
    textNodes.forEach(node => { if (!ignored.has(node.parentElement?.tagName)) node.nodeValue = translate(node.nodeValue); });
    root.querySelectorAll?.("input[placeholder], textarea[placeholder], [title], [aria-label]").forEach(el => {
      ["placeholder", "title", "aria-label"].forEach(attr => { if (el.hasAttribute(attr)) el.setAttribute(attr, translate(el.getAttribute(attr))); });
    });
  };
  const run = () => walk(document.body);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run, { once: true }); else run();
  new MutationObserver(run).observe(document.body, { childList: true, subtree: true });
})();
