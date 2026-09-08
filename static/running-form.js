(() => {
  const I = Object.assign({
    title: "Sungeum AI Running Coach", working: "Sungeum is analyzing your run", done_stamp: "Sungeum checked it", landing_frame: "AI foot-strike frame", foot_zoom: "Foot-strike close-up", coach: "Sungeum's coaching note", next_goal: "One thing to change next run", save_image: "Save SNS result image", save_done: "Your running result was saved", generic_error: "Something went wrong while analyzing the video. Please try again.", mediapipe_error: "AI pose tracking is getting ready again. Press analyze once more in a moment.", range_knee: "Recommended range 105–125°", range_trunk: "Recommended range 6–14°", steps: ["Check video", "Find joints", "Analyze strike", "Prepare coaching"]
  }, window.RUNNING_I18N || {});
  Object.assign(I, { flow_upload: "Upload running video", flow_analyze: "Sungeum AI analysis", flow_share: "Share coaching result", coach_prompt: "Show your video to Sungeum", upload_heading: "Upload your side-view run", upload_copy: "A 5–10 second clip showing your head to toes works best. Keep your feet and the ground visible for a clearer review.", capture_tip: "A steady side camera and bright lighting improve analysis quality. Results can vary with camera angle, speed and lighting.", credit_note: "Running coaching is free.", credits: "FREE", how_to: "How to record a good clip", step1_title: "Keep the camera steady", step1_copy: "Use a clear side view without shaking", step2_title: "Show your full body and feet", step2_copy: "Keep your head, toes and ground in frame", step3_title: "5–10 seconds is enough", step3_copy: "Bright light and 60fps or higher are recommended", coach_subtitle: "Analysis · coaching · report review", pace_easy: "Easy jog", pace_marathon: "Marathon pace", pace_10k: "10K pace", pace_fast: "Fast run", rear_view: "Rear view · coming soon", terms: "Terms", privacy: "Privacy", refund: "Refund policy", contact: "Contact", assistant_greeting: "Hi, I’m Sungeum 🐶", assistant_status: "Let me handle today’s promo", assistant_running_status: "View promo and running together" }, window.RUNNING_I18N || {});
  const form = document.getElementById("runningForm");
  if (!form) return;
  const input = document.getElementById("videoInput");
  const zone = document.getElementById("uploadZone");
  const panel = document.getElementById("previewPanel");
  const preview = document.getElementById("videoPreview");
  const canvas = document.getElementById("poseCanvas");
  const summary = document.getElementById("fileSummary");
  const consent = document.getElementById("consentCheck");
  const button = document.getElementById("analyzeButton");
  const status = document.getElementById("statusPanel");
  let previewUrl = null;
  const selectedFile = () => input.files && input.files[0];
  const sync = () => { button.disabled = !(selectedFile() && consent.checked); };
  const friendlyError = error => {
    const message = String(error?.message || error || "");
    if (/timestamp|CalculatorGraph|Packet|mediapipe/i.test(message)) {
      return "AI 자세 추적을 다시 준비하고 있어요. 잠시 후 분석 버튼을 다시 눌러주세요.";
    }
    return message || "영상 분석 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.";
  };
  const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);

  // Presentation-only localization. Pose extraction remains unchanged; the
  // running coach is intentionally free while marketing generation uses credits.
  function applyLocalizedRunningUi() {
    const setText = (selector, value) => { const node = document.querySelector(selector); if (node && value && node.textContent !== value) node.textContent = value; };
    setText(".run-kicker", I.title);
    setText(".run-hero h1", I.hero_title);
    setText(".run-hero-copy > p", I.hero_desc);
    setText(".run-coach-flow div:nth-child(1) span", I.flow_upload);
    setText(".run-coach-flow div:nth-child(2) span", I.flow_analyze);
    setText(".run-coach-flow div:nth-child(3) span", I.flow_share);
    setText(".col-lg-8 .pf-card .pf-eyebrow", I.coach_prompt);
    setText(".col-lg-8 .pf-card h2", I.upload_heading);
    setText(".col-lg-8 .pf-card > p", I.upload_copy);
    setText(".col-lg-8 .pf-card .alert", I.capture_tip);
    setText("#uploadZone strong", I.upload_title);
    setText("#uploadZone span", I.upload_hint);
    setText("#analyzeButton", I.analyze);
    setText("#consentCheck + label", I.consent);
    setText("#runningForm .d-flex.justify-content-between span", I.credit_note);
    setText("#runningForm .d-flex.justify-content-between strong", I.credits);
    const helper = document.querySelectorAll(".col-lg-4 .pf-card")[0];
    if (helper) {
      setText(".col-lg-4 .pf-card .pf-eyebrow", I.how_to);
      const helperTitles = helper.querySelectorAll(".run-step strong");
      const helperCopies = helper.querySelectorAll(".run-step .small");
      [I.step1_title, I.step2_title, I.step3_title].forEach((value, index) => { if (helperTitles[index]) helperTitles[index].textContent = value; });
      [I.step1_copy, I.step2_copy, I.step3_copy].forEach((value, index) => { if (helperCopies[index]) helperCopies[index].textContent = value; });
    }
    const coachCard = document.querySelectorAll(".col-lg-4 .pf-card")[1];
    if (coachCard) { const coachTitle = coachCard.querySelector("strong"); const coachSubtitle = coachCard.querySelector(".small.text-secondary"); const coachQuote = coachCard.querySelector("p.small"); if (coachTitle && I.coach) coachTitle.textContent = I.coach; if (coachSubtitle && I.coach_subtitle) coachSubtitle.textContent = I.coach_subtitle; if (coachQuote && I.coach_quote) coachQuote.textContent = `“${I.coach_quote}”`; }
    const assistantCallout = document.querySelector(".sungeum-click-callout"); if (assistantCallout && I.assistant_greeting) assistantCallout.textContent = I.assistant_greeting;
    const assistantStatus = document.querySelector(".sungeum-assistant-trigger .sungeum-live-status"); if (assistantStatus && I.assistant_status) assistantStatus.textContent = I.assistant_status;
    const metricLabels = [I.metric_score, I.metric_runner, I.metric_strike, I.metric_knee, I.metric_trunk, I.metric_detection];
    document.querySelectorAll("#statusPanel .run-check").forEach((check, index) => { const labels = check.querySelectorAll("small"); if (metricLabels[index] && labels[0]) labels[0].textContent = metricLabels[index]; if (index === 2 && labels[1]) labels[1].textContent = `${I.metric_confidence} ${String(labels[1].textContent).split(" ").pop()}`; });
    const paceLabel = document.querySelector("label[for='paceSelect']"); if (paceLabel && I.pace_label) paceLabel.textContent = I.pace_label;
    const viewLabel = document.querySelector("label[for='viewSelect']"); if (viewLabel && I.view_label) viewLabel.textContent = I.view_label;
    [["easy", I.pace_easy], ["marathon", I.pace_marathon], ["10k", I.pace_10k], ["fast", I.pace_fast]].forEach(([value, label]) => { const option = document.querySelector(`#paceSelect option[value='${value}']`); if (option && label) option.textContent = label; });
    const sideOption = document.querySelector("#viewSelect option[value='side']"); if (sideOption && I.side) sideOption.textContent = I.side;
    const rearOption = document.querySelector("#viewSelect option[value='rear']"); if (rearOption && I.rear_view) rearOption.textContent = I.rear_view;
    const footerLabels = [I.terms, I.privacy, I.refund, I.contact];
    document.querySelectorAll("footer a, .pf-footer a").forEach((link, index) => { if (footerLabels[index]) link.textContent = footerLabels[index]; });
    document.querySelectorAll(".run-progress-steps span").forEach((node, index) => { if (I.steps?.[index]) node.textContent = I.steps[index]; });
    setText(".run-progress-head strong", I.working);
    setText("#runShareArea h3", I.share_title);
    const resultSections = document.querySelectorAll("#statusPanel .run-result-section strong");
    if (resultSections[0]) resultSections[0].textContent = I.strengths;
    if (resultSections[1]) resultSections[1].textContent = I.improvement;
    document.querySelectorAll("#statusPanel button").forEach(button => {
      if (/SNS 결과 이미지 저장|Save SNS result image|SNS結果画像|บันทึกภาพผลลัพธ์|保存 SNS|Guardar imagen/.test(button.textContent)) button.textContent = I.save_image;
    });
    document.querySelectorAll("#statusPanel .small").forEach(node => {
      if (/생성 기록에 저장하는 중|Saving to history|履歴に保存中|กำลังบันทึกประวัติ|正在保存到记录|Guardando en el historial/.test(node.textContent)) node.textContent = I.saving;
    });
    if (status) {
      const replacements = [["순금이가 찾은 잘한 점", I.strengths], ["다음 러닝에서 바꿀 한 가지", I.improvement], ["순금이 코치의 SNS 공유 결과지", I.share_title], ["AI 영상 기반 참고 분석이며 의료 진단이 아닙니다. 촬영 각도·속도·조명에 따라 판정이 달라질 수 있어요.", I.disclaimer]];
      const walker = document.createTreeWalker(status, NodeFilter.SHOW_TEXT);
      const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(node => replacements.forEach(([from, to]) => { if (to && node.nodeValue.includes(from)) node.nodeValue = node.nodeValue.replace(from, to); }));
    }
  }
  const RESULT_TEXT = {
    "측면 자세가 선명해 관절 움직임을 안정적으로 추적했어요.": "strength_clear", "상체 기울기가 자연스러운 추진 범위에 있어요.": "strength_trunk", "무릎 굴곡이 충격 흡수와 추진을 함께 만들 수 있는 범위예요.": "strength_knee", "발바닥 중앙에 가까운 착지 패턴이 감지됐어요.": "strength_midfoot",
    "지금 상체가 조금 앞으로 숙여져 있어. 허리만 굽히지 말고 발목부터 몸 전체를 살짝 기울여서 달려봐. 그러면 자세가 더 편안하고 안정적으로 좋아질 거야.": "improve_trunk_forward", "지금 상체가 조금 곧게 서 있어. 발목부터 몸 전체를 앞쪽으로 살짝 기울여서 달려봐. 그러면 앞으로 나가는 힘을 더 편하게 받을 수 있을 거야.": "improve_trunk_upright", "보폭을 지금보다 조금만 줄여봐. 발이 몸 바로 아래에 닿는 느낌으로 달리면 충격을 줄이고 리듬도 더 편해질 거야.": "improve_stride", "뒤꿈치가 몸보다 너무 앞에서 닿지 않는지 한번 확인해봐. 케이던스를 3~5%만 높이면 착지가 몸 아래로 들어오는 데 도움이 될 거야.": "improve_rear", "앞꿈치로 잘 달리고 있어. 다만 종아리에 힘이 몰리지 않게 뒤꿈치가 지면으로 자연스럽게 내려오도록 해봐. 그러면 오래 달릴 때 더 편해질 거야.": "improve_fore"
  };
  function localizeResult(result) {
    const strikeKey = result.strikeType === "포어풋형" ? "strike_forefoot" : result.strikeType === "리어풋형" ? "strike_rearfoot" : "strike_midfoot";
    const runnerParts = String(result.runnerType || "").split(" · ");
    const runnerKey = runnerParts[1] === "전방 추진형" ? "runner_forward" : runnerParts[1] === "안정 중심형" ? "runner_stable" : "runner_balanced";
    return { ...result, strikeType: I[strikeKey] || result.strikeType, runnerType: `${I[strikeKey] || runnerParts[0]} · ${I[runnerKey] || runnerParts[1] || ""}`.trim(), strengths: (result.strengths || []).map(item => I[RESULT_TEXT[item]] || item), improvements: (result.improvements || []).map(item => I[RESULT_TEXT[item]] || item) };
  }
  applyLocalizedRunningUi();
  setTimeout(applyLocalizedRunningUi, 0);
  setTimeout(applyLocalizedRunningUi, 250);
  const localizationTimer = setInterval(applyLocalizedRunningUi, 500);
  setTimeout(() => clearInterval(localizationTimer), 5000);
  // The shared assistant widget periodically updates its status (for example
  // when it enters a listening state). Keep the running page's selected
  // language authoritative so that late widget updates cannot reintroduce
  // Korean text into an otherwise translated page.
  setInterval(applyLocalizedRunningUi, 1000);
  let localizing = false;
  const localizedUiObserver = new MutationObserver(() => {
    if (localizing) return;
    localizing = true;
    requestAnimationFrame(() => { applyLocalizedRunningUi(); localizing = false; });
  });
  localizedUiObserver.observe(status, { childList: true, subtree: true });

  const progressStages = I.steps || ["영상 확인", "관절 찾기", "착지 분석", "코칭 정리"];
  const progressCopy = progress => progress < 45 ? (I.finding || I.working) : progress < 80 ? (I.comparing || I.working) : (I.summarizing || I.working);
  function showCoachProgress(message, percent = 5) {
    const activeIndex = Math.min(3, Math.floor(Math.max(0, percent - 1) / 25));
    status.className = "run-progress-card mt-4";
    applyLocalizedRunningUi();
    status.innerHTML = `<div class="run-progress-head"><img class="sungeum-alive is-working" src="/static/brand/sungeum-running-coach-goggles-v1-transparent.png" alt=""><div><strong>순금이 코치가 분석하고 있어요</strong><div class="small text-secondary mt-1">${escapeHtml(message)}</div></div></div><div class="run-progress-track"><div class="run-progress-bar" style="width:${Math.max(5, percent)}%"></div></div><div class="run-progress-steps">${progressStages.map((stage,index)=>`<span class="${index <= activeIndex ? "is-active" : ""}">${stage}</span>`).join("")}</div>`;
  }

  async function saveRunningHistory(result, card) {
    const response = await fetch("/running-form/history", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...result,coachMessage:result.improvements[0]||"",image:card.toDataURL("image/png")})});
    const saved = await response.json();
    if (!response.ok || !saved.ok) throw new Error(saved.error || "생성 기록에 저장하지 못했어요.");
    return saved;
  }

  function mountQuickFeedback(container, historyId) {
    const copy = window.RUNNING_FEEDBACK_I18N || {};
    const card = document.createElement("section");
    card.className = "run-quick-feedback";
    card.innerHTML = `<strong>${escapeHtml(copy.title || "How was Sungeum’s result? 🐶")}</strong><p>${escapeHtml(copy.prompt || "One tap helps us improve the next result.")}</p><div class="d-flex flex-wrap gap-2"><button type="button" class="feedback-choice" data-rating="5">${escapeHtml(copy.helpful || "👍 It helped")}</button><button type="button" class="feedback-choice" data-rating="3">${escapeHtml(copy.neutral || "😐 It was okay")}</button><button type="button" class="feedback-choice" data-rating="2">${escapeHtml(copy.not_helpful || "👎 Needs work")}</button></div><div class="feedback-extra d-none"><label class="small fw-semibold d-block mt-3">${escapeHtml(copy.comment || "Add a note (optional)")}</label><textarea maxlength="3000" placeholder="${escapeHtml(copy.placeholder || "Tell us one thing you liked or would change")}"></textarea><button type="button" class="feedback-submit">${escapeHtml(copy.send || "Send feedback")}</button></div><div class="feedback-thanks d-none">${escapeHtml(copy.thanks || "Thanks for sharing! 🐶✨")}</div>`;
    container.appendChild(card);
    const choices = [...card.querySelectorAll("[data-rating]")];
    const extra = card.querySelector(".feedback-extra");
    const textarea = card.querySelector("textarea");
    const submit = card.querySelector(".feedback-submit");
    const thanks = card.querySelector(".feedback-thanks");
    let rating = null;
    choices.forEach(choice => choice.addEventListener("click", () => { rating = Number(choice.dataset.rating); choices.forEach(item => item.classList.toggle("is-selected", item === choice)); extra.classList.remove("d-none"); textarea.focus(); }));
    submit.addEventListener("click", async () => {
      if (!rating) return;
      submit.disabled = true;
      try {
        const response = await fetch("/feedback/quick", {method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:new URLSearchParams({history_id:String(historyId),rating:String(rating),comment:textarea.value})});
        if (!response.ok) throw new Error("feedback failed");
        extra.classList.add("d-none"); choices.forEach(item => { item.disabled = true; item.classList.remove("is-selected"); }); thanks.classList.remove("d-none");
      } catch (error) { submit.disabled = false; window.location.href = `/feedback?history_id=${encodeURIComponent(historyId)}`; }
    });
  }

  async function makeShareCard(result, analysisFrame) {
    return window.createRunningReport(result, analysisFrame, I);
  }

  function showFile(file) {
    if (!file) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    preview.src = previewUrl;
    summary.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)}MB`;
    panel.classList.remove("d-none");
    canvas.classList.add("d-none");
    sync();
  }

  input.addEventListener("change", () => showFile(selectedFile()));
  consent.addEventListener("change", sync);
  ["dragenter", "dragover"].forEach(name => zone.addEventListener(name, event => { event.preventDefault(); zone.classList.add("is-dragging"); }));
  ["dragleave", "drop"].forEach(name => zone.addEventListener(name, event => { event.preventDefault(); zone.classList.remove("is-dragging"); }));
  zone.addEventListener("drop", event => {
    const file = event.dataTransfer.files[0]; if (!file) return;
    const transfer = new DataTransfer(); transfer.items.add(file); input.files = transfer.files; showFile(file);
  });

  form.addEventListener("submit", async event => {
    event.preventDefault(); button.disabled = true;
    button.textContent = I.working || "Sungeum is analyzing your run";
    document.dispatchEvent(new CustomEvent("sungeum:state", { detail: { state: "working" } }));
    showCoachProgress(I.finding || I.working, 8);
    try {
      const response = await fetch("/running-form/preflight", { method: "POST", body: new FormData(form) });
      const preflight = await response.json();
      if (!response.ok || !preflight.ok) throw new Error(preflight.error || "영상을 확인하지 못했어요.");
      showCoachProgress(I.comparing || I.working, 20);
      const { analyzePose } = await import("/static/running-pose-analyzer.js");
      canvas.classList.remove("d-none");
      const rawResult = await analyzePose(preview, canvas, progress => {
        const message = progressCopy(progress);
        showCoachProgress(message, progress);
      });
      const result = localizeResult(rawResult);
      const strengths = result.strengths.map(item => `<li>${escapeHtml(item)}</li>`).join("");
      const improvements = result.improvements.map(item => `<li>${escapeHtml(item)}</li>`).join("");
      status.className = "mt-4";
      document.dispatchEvent(new CustomEvent("sungeum:state", { detail: { state: "approved", duration: 1400 } }));
      status.innerHTML = `<div class="alert alert-success"><strong>${escapeHtml(I.complete || "Sungeum AI running analysis complete")}</strong><br>${escapeHtml(I.complete_desc || "Your coaching result is based on real video frames.")}</div>
        <div class="row g-2">
          <div class="col-6"><div class="run-check" data-status="pass"><small>${escapeHtml(I.metric_score || "Overall running-form score")}</small><br><strong>${result.score}</strong></div></div>
          <div class="col-6"><div class="run-check" data-status="pass"><small>${escapeHtml(I.metric_runner || "Runner type")}</small><br><strong>${escapeHtml(result.runnerType)}</strong></div></div>
          <div class="col-6"><div class="run-check"><small>${escapeHtml(I.metric_strike || "Foot-strike type")}</small><br><strong>${result.strikeType}</strong><br><small>${escapeHtml(I.metric_confidence || "Confidence")} ${result.strikeConfidence}%</small></div></div>
          <div class="col-6"><div class="run-check"><small>${escapeHtml(I.metric_knee || "Average knee angle")}</small><br><strong>${result.averageKneeAngle}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>${escapeHtml(I.metric_trunk || "Average trunk lean")}</small><br><strong>${result.averageTrunkLean}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>${escapeHtml(I.metric_detection || "Joint detection rate")}</small><br><strong>${result.detectionRate}%</strong></div></div>
        </div><div class="run-result-section mt-3"><strong>${escapeHtml(I.strengths || "What Sungeum found you did well")}</strong><ul class="mt-2 mb-0">${strengths}</ul></div><div class="run-result-section mt-3"><strong>${escapeHtml(I.improvement || "One thing to change next run")}</strong><ul class="mt-2 mb-0">${improvements}</ul></div><div id="runShareArea" class="mt-3"><h3 class="h5 fw-bold">${escapeHtml(I.share_title || "Sungeum's SNS share result")}</h3></div><div class="small text-secondary mt-3">${escapeHtml(I.disclaimer || "This is an AI video-based reference analysis, not a medical diagnosis.")}</div>`;
      const card = await makeShareCard(result, canvas), shareArea = document.getElementById("runShareArea"); shareArea.appendChild(card);
      const download = document.createElement("button"); download.type="button"; download.className="btn btn-success w-100 fw-bold"; download.textContent=I.save_image || "Save SNS result image"; download.onclick=()=>{const link=document.createElement("a");link.download="sungeum-running-form-result.png";link.href=card.toDataURL("image/png");link.click()};shareArea.appendChild(download);
      const saveState=document.createElement("div");saveState.className="small text-secondary mt-2";saveState.textContent=I.saving || "Saving to history…";shareArea.appendChild(saveState);
      try{const saved=await saveRunningHistory(result,card);saveState.innerHTML=I.saved || "✓ Saved to history · View history";saveState.dataset.historyId=saved.history_id;mountQuickFeedback(shareArea,saved.history_id)}catch(saveError){saveState.textContent=`${I.generic_error || "Something went wrong"}: ${friendlyError(saveError)}`;mountQuickFeedback(shareArea,null)}
    } catch (error) {
      document.dispatchEvent(new CustomEvent("sungeum:state", { detail: { state: "failed", duration: 1800 } }));
      status.className = "alert alert-danger mt-4"; status.textContent = friendlyError(error);
    } finally {
      button.textContent = I.analyze || "Ask Sungeum to analyze for free"; sync();
    }
  });
})();
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('img[src*="sungeum-3d-official.png"]').forEach((image) => {
    image.src = "/static/brand/sungeum-running-coach-goggles-v1-transparent.png";
  });
});
