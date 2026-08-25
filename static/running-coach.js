(function () {
  const state = { condition: null, minutes: null, goal: null };
  const submit = document.getElementById("coach-submit");
  const status = document.getElementById("coach-status");
  const resultBox = document.getElementById("coach-result");
  document.querySelectorAll(".choice-grid").forEach((group) => {
    group.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-value]");
      if (!button) return;
      group.querySelectorAll("button").forEach((item) => item.classList.remove("selected"));
      button.classList.add("selected");
      state[group.dataset.field] = button.dataset.value;
      submit.disabled = !(state.condition && state.minutes && state.goal);
    });
  });
  submit.addEventListener("click", async () => {
    submit.disabled = true;
    status.textContent = "순금이가 오늘 계획을 정리하고 있어…";
    try {
      const response = await fetch("/running-coach/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(state) });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "코칭을 만들지 못했어.");
      const r = data.result;
      resultBox.innerHTML = `<h2 class="result-title">${escapeHtml(r.title)}</h2>
        <div class="result-item"><h3>오늘의 계획</h3><p>${escapeHtml(r.plan)}</p></div>
        <div class="result-item"><h3>추천 강도</h3><p>${escapeHtml(r.intensity)}</p></div>
        <div class="result-item"><h3>워밍업</h3><p>${escapeHtml(r.warmup)}</p></div>
        <div class="result-item"><h3>주의사항</h3><p>${escapeHtml(r.caution)}</p></div>
        <div class="result-item"><h3>마무리</h3><p>${escapeHtml(r.cooldown)}</p></div>
        <div class="result-cheer"><img class="result-mascot" src="/static/brand/sungeum-running-coach-goggles-v1-transparent.png" alt="순금이 러닝코치"><span>${escapeHtml(r.cheer)}</span></div><section class="running-coach-feedback mt-4"><strong>순금이 러닝 코치는 어땠어? 🐶</strong><p>다음 러닝 계획을 더 잘 만들 수 있게 한 번만 알려줘.</p><div class="feedback-buttons"><button type="button" data-rating="5">👍 도움이 됐어</button><button type="button" data-rating="3">🙂 보통이야</button><button type="button" data-rating="1">🤔 아쉬워</button></div><textarea maxlength="3000" placeholder="짧은 후기 (선택)"></textarea><button type="button" class="feedback-send" disabled>후기 보내기</button><div class="feedback-thanks" hidden>고마워! 다음 러닝도 더 잘 도와줄게 🐶✨</div></section>`;
      const feedback = resultBox.querySelector('.running-coach-feedback');
      let feedbackRating = 0;
      feedback.querySelectorAll('[data-rating]').forEach((item) => item.addEventListener('click', () => { feedbackRating = Number(item.dataset.rating); feedback.querySelectorAll('[data-rating]').forEach((button) => button.classList.toggle('selected', button === item)); feedback.querySelector('.feedback-send').disabled = false; }));
      feedback.querySelector('.feedback-send').addEventListener('click', async () => { const send = feedback.querySelector('.feedback-send'); send.disabled = true; try { const response = await fetch('/api/running-coach/feedback', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating:feedbackRating,comment:feedback.querySelector('textarea').value.trim()})}); if (!response.ok) throw new Error('feedback failed'); feedback.querySelector('.feedback-buttons').hidden = true; feedback.querySelector('textarea').hidden = true; send.hidden = true; feedback.querySelector('.feedback-thanks').hidden = false; } catch (error) { send.disabled = false; } });
      resultBox.hidden = false;
      resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
      status.textContent = data.source === "fallback" ? "기본 안전 코칭으로 안내했어." : "순금이가 너에게 맞춰 정리했어.";
    } catch (error) {
      status.textContent = error.message;
      submit.disabled = false;
    }
  });
  function escapeHtml(value) { const el = document.createElement("div"); el.textContent = value || ""; return el.innerHTML; }
})();
