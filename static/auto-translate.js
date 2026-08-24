(function () {
  "use strict";
  // The app has its own translations for the core UI.  Some older coach and
  // helper screens still contain Korean copy (including text inserted by
  // JavaScript). When English is selected, let Google's page translator cover
  // those legacy strings as a final fallback so the whole screen stays in the
  // selected language.
  if (document.documentElement.lang !== "en") return;

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
