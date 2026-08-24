(function () {
  "use strict";
  const labels = window.PF_MENU_I18N || {};
  if (!Object.keys(labels).length) return;

  const routes = [
    ["dashboard", "/dashboard"], ["ads", "/content"], ["ads", "/ads-generator"], ["sns", "/sns"], ["blog", "/blog"],
    ["poster", "/poster"], ["running", "/running-form"],
    ["speaking", "/speaking-coach"], ["reviews", "/reviews"],
    ["history", "/history"], ["credits", "/credits"]
  ];

  function setLabel(anchor, label) {
    if (!anchor || !label) return;
    const textNodes = [];
    anchor.childNodes.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) textNodes.push(node);
    });
    if (textNodes.length) {
      textNodes[0].nodeValue = " " + label;
      textNodes.slice(1).forEach((node) => { node.nodeValue = ""; });
    } else {
      anchor.appendChild(document.createTextNode(" " + label));
    }
    anchor.setAttribute("data-pf-menu-key", label);
  }

  function apply(root) {
    const scope = root || document;
    scope.querySelectorAll("a[href], button").forEach((el) => {
      const href = el.getAttribute("href") || el.getAttribute("data-href") || "";
      const match = routes.find(([, path]) => href === path || href.startsWith(path + "?"));
      if (match) setLabel(el, labels[match[0]]);
    });
  }

  const run = () => apply(document);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run, { once: true });
  else run();
  new MutationObserver(run).observe(document.documentElement, { childList: true, subtree: true });
})();
