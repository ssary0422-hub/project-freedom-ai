(function () {
  "use strict";
  // The app has its own translations for the core UI.  Some older coach and
  // helper screens still contain Korean copy (including text inserted by
  // JavaScript). When English is selected, let Google's page translator cover
  // those legacy strings as a final fallback so the whole screen stays in the
  // selected language.
  if (document.documentElement.lang !== "en") return;

  // Tell the widget to apply English immediately; users should not have to
  // open a second language menu after choosing English in the app.
  document.cookie = "googtrans=/ko/en; path=/";

  // Keep the mascot's proper name as a name, rather than translating it as
  // the literal phrase “pure gold”.
  const protectSungeumName = () => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (!node.nodeValue || !node.nodeValue.includes("순금")) return;
      node.nodeValue = node.nodeValue.replaceAll("순금이", "Sungeum").replaceAll("순금", "Sungeum");
    });
  };
  if (document.body) protectSungeumName();

  window.googleTranslateElementInit = function () {
    if (!window.google || !google.translate) return;
    new google.translate.TranslateElement({
      pageLanguage: "ko",
      includedLanguages: "en",
      autoDisplay: false,
      multilanguagePage: true,
    }, "google_translate_fallback");
  };

  const style = document.createElement("style");
  style.textContent = `
    #google_translate_fallback { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }
    .goog-te-banner-frame, .skiptranslate { display: none !important; }
    body { top: 0 !important; }
  `;
  document.head.appendChild(style);

  const mount = document.createElement("div");
  mount.id = "google_translate_fallback";
  mount.setAttribute("aria-hidden", "true");
  document.body.appendChild(mount);

  const script = document.createElement("script");
  script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
  script.async = true;
  script.onerror = () => mount.remove();
  document.head.appendChild(script);
})();
