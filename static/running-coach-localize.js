(function () {
  const I = window.RUNNING_COACH_I18N || {};
  if (!Object.keys(I).length) return;
  const set = (selector, value) => { const n = document.querySelector(selector); if (n && value) n.textContent = value; };
  const setAll = (selector, values) => document.querySelectorAll(selector).forEach((n, i) => { if (values[i]) n.textContent = values[i]; });
  function apply() {
    set('.running-coach-page .eyebrow', I.eyebrow); set('.coach-hero h1', I.title); set('.coach-hero > div > p', I.desc);
    const questions = document.querySelectorAll('.coach-question strong');
    [I.condition, I.minutes, I.goal].forEach((v, i) => { if (questions[i] && v) questions[i].textContent = v; });
    setAll('[data-field="condition"] button', [I.good, I.normal, I.tired, I.pain]);
    setAll('[data-field="minutes"] button', ['20', '30', '45', '60+']);
    setAll('[data-field="goal"] button', [I.easy, I.fitness, I.weight, I.race]);
    set('#coach-submit', I.submit);
    const result = document.getElementById('coach-result');
    if (result && !result.hidden) {
      setAll('.result-item h3', [I.plan, I.intensity, I.warmup, I.caution, I.cooldown]);
      set('.running-coach-feedback strong', I.feedback_title); set('.running-coach-feedback p', I.feedback_prompt);
      setAll('.running-coach-feedback [data-rating]', [I.helpful, I.neutral, I.not_helpful]);
      const feedbackInput = document.querySelector('.running-coach-feedback textarea'); if (feedbackInput && I.feedback_placeholder) feedbackInput.placeholder = I.feedback_placeholder;
      set('.feedback-send', I.feedback_send); set('.feedback-thanks', I.thanks);
    } else if (document.getElementById('coach-status')?.textContent) set('#coach-status', I.thinking);
  }
  apply();
  let busy = false;
  new MutationObserver(() => { if (busy) return; busy = true; requestAnimationFrame(() => { apply(); busy = false; }); }).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
