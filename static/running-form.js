(() => {
  const I = Object.assign({
    title: "Sungeum AI Running Coach", working: "Sungeum is analyzing your run", done_stamp: "Sungeum checked it", landing_frame: "AI foot-strike frame", foot_zoom: "Foot-strike close-up", coach: "Sungeum's coaching note", next_goal: "One thing to change next run", save_image: "Save SNS result image", save_done: "Your running result was saved", generic_error: "Something went wrong while analyzing the video. Please try again.", mediapipe_error: "AI pose tracking is getting ready again. Press analyze once more in a moment.", range_knee: "Recommended range 105–125°", range_trunk: "Recommended range 6–14°", steps: ["Check video", "Find joints", "Analyze strike", "Prepare coaching"]
  }, window.RUNNING_I18N || {});
  Object.assign(I, { flow_upload: "Upload running video", flow_analyze: "Sungeum AI analysis", flow_share: "Share coaching result", coach_prompt: "Show your video to Sungeum", upload_heading: "Upload your side-view run", upload_copy: "A 5–10 second clip showing your head to toes works best. Keep your feet and the ground visible for a clearer review.", capture_tip: "A steady side camera and bright lighting improve analysis quality. Results can vary with camera angle, speed and lighting.", credit_note: "Credits are deducted only when analysis succeeds.", credits: "3 credits", how_to: "How to record a good clip", step1_title: "Keep the camera steady", step1_copy: "Use a clear side view without shaking", step2_title: "Show your full body and feet", step2_copy: "Keep your head, toes and ground in frame", step3_title: "5–10 seconds is enough", step3_copy: "Bright light and 60fps or higher are recommended", coach_subtitle: "Analysis · coaching · report review", pace_easy: "Easy jog", pace_marathon: "Marathon pace", pace_10k: "10K pace", pace_fast: "Fast run", rear_view: "Rear view · coming soon", terms: "Terms", privacy: "Privacy", refund: "Refund policy", contact: "Contact", assistant_greeting: "Hi, I’m Sungeum 🐶", assistant_status: "Let me handle today’s promo", assistant_running_status: "View promo and running together" }, window.RUNNING_I18N || {});
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

  // Presentation-only localization. Pose extraction, scoring and credit flow
  // remain unchanged so the existing running feature keeps the same behavior.
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
    status.innerHTML = `<div class="run-progress-head"><img class="sungeum-alive is-working" src="/static/brand/sungeum-3d-official.png" alt=""><div><strong>순금이 코치가 분석하고 있어요</strong><div class="small text-secondary mt-1">${escapeHtml(message)}</div></div></div><div class="run-progress-track"><div class="run-progress-bar" style="width:${Math.max(5, percent)}%"></div></div><div class="run-progress-steps">${progressStages.map((stage,index)=>`<span class="${index <= activeIndex ? "is-active" : ""}">${stage}</span>`).join("")}</div>`;
  }

  function roundedClip(ctx, x, y, width, height, radius = 28) {
    ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); ctx.clip();
  }

  function drawContain(ctx, image, x, y, width, height) {
    const scale = Math.min(width / image.width, height / image.height), drawWidth = image.width * scale, drawHeight = image.height * scale;
    const drawX = x + (width - drawWidth) / 2, drawY = y + (height - drawHeight) / 2;
    const backdropScale = Math.max(width / image.width, height / image.height), backdropWidth = image.width * backdropScale, backdropHeight = image.height * backdropScale;
    ctx.save(); roundedClip(ctx, x, y, width, height); ctx.filter = "blur(18px)"; ctx.globalAlpha = .46; ctx.drawImage(image, x + (width - backdropWidth) / 2 - 12, y + (height - backdropHeight) / 2 - 12, backdropWidth + 24, backdropHeight + 24); ctx.filter = "none"; ctx.globalAlpha = 1; ctx.fillStyle = "rgba(7,17,31,.30)"; ctx.fillRect(x, y, width, height); ctx.drawImage(image, drawX, drawY, drawWidth, drawHeight); ctx.restore();
  }

  function drawApprovalStamp(ctx, x, y) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(-.07); ctx.fillStyle = "rgba(16,185,129,.13)"; ctx.strokeStyle = "#61e6d3"; ctx.lineWidth = 3; ctx.beginPath(); ctx.roundRect(0, 0, 238, 74, 20); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#61e6d3"; [[34,39,15,13],[18,20,6,8],[31,13,6,8],[44,15,6,8],[54,25,6,8]].forEach(([cx,cy,rx,ry])=>{ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.fill()});
    ctx.font = '800 23px "Malgun Gothic", sans-serif'; ctx.fillText("순금 검수 완료", 72, 34); ctx.fillStyle = "#a7f3d0"; ctx.font = '600 16px "Malgun Gothic", sans-serif'; ctx.fillText("러닝폼 AI 결과 확인", 72, 57); ctx.restore();
  }

  function nextScoreTip(result) {
    if (result.averageTrunkLean > 14) return "다음 목표 · 상체 기울기를 권장 범위로 조절하면 약 +4점";
    if (result.averageTrunkLean < 6) return "다음 목표 · 상체를 조금만 기울이면 추진 점수 향상 가능";
    if (result.averageKneeAngle < 105 || result.averageKneeAngle > 125) return "다음 목표 · 착지 때 무릎 각도를 조절하면 점수 향상 가능";
    return "다음 목표 · 같은 조건으로 다시 촬영해 자세 변화를 비교해봐";
  }

  async function saveRunningHistory(result, card) {
    const response = await fetch("/running-form/history", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...result,coachMessage:result.improvements[0]||"",image:card.toDataURL("image/png")})});
    const saved = await response.json();
    if (!response.ok || !saved.ok) throw new Error(saved.error || "생성 기록에 저장하지 못했어요.");
    return saved;
  }

  function drawFootInset(ctx, image, focus, x, y, size) {
    if (!focus) return;
    const sourceSize = Math.min(image.width, image.height) * .34;
    const sourceX = Math.max(0, Math.min(image.width - sourceSize, focus.x * image.width - sourceSize / 2));
    const sourceY = Math.max(0, Math.min(image.height - sourceSize, focus.y * image.height - sourceSize * .62));
    ctx.save(); roundedClip(ctx, x, y, size, size, 22); ctx.drawImage(image, sourceX, sourceY, sourceSize, sourceSize, x, y, size, size); ctx.restore();
    ctx.strokeStyle = "#61e6d3"; ctx.lineWidth = 5; ctx.strokeRect(x + 2, y + 2, size - 4, size - 4);
    ctx.fillStyle = "rgba(7,17,31,.84)"; ctx.fillRect(x + 10, y + size - 39, size - 20, 30); ctx.fillStyle = "#61e6d3"; ctx.font = '700 18px "Malgun Gothic", sans-serif'; ctx.fillText("착지 확대", x + 24, y + size - 17);
  }

  function loadCoachMascot() {
    return new Promise(resolve => {
      const mascot = new Image();
      mascot.onload = () => resolve(mascot);
      mascot.onerror = () => resolve(null);
      mascot.src = "/static/brand/sungeum-3d-official.png";
    });
  }

  async function makeShareCard(result, analysisFrame) {
    const card = document.createElement("canvas"); card.width = 1080; card.height = 1350; card.className = "run-share-card";
    const ctx = card.getContext("2d"), gradient = ctx.createLinearGradient(0, 0, 1080, 1350);
    gradient.addColorStop(0, "#07111f"); gradient.addColorStop(.55, "#12344c"); gradient.addColorStop(1, "#0d766f"); ctx.fillStyle = gradient; ctx.fillRect(0, 0, 1080, 1350);
    const mascot = await loadCoachMascot();
    if (mascot) {
      ctx.save();
      ctx.drawImage(mascot, 830, 18, 176, 218); ctx.restore();
    }
    ctx.fillStyle = "#61e6d3"; ctx.font = "800 30px Arial"; ctx.fillText("SUNGEUM AI RUNNING COACH", 76, 95);
    ctx.fillStyle = "#fff"; ctx.font = '900 70px "Malgun Gothic", sans-serif'; ctx.fillText("순금이 코치의 러닝폼 리포트", 76, 205);
    ctx.fillStyle = "#61e6d3"; ctx.font = "900 170px Arial"; ctx.fillText(String(result.score), 70, 440);
    ctx.fillStyle = "#fff"; ctx.font = "800 38px Arial"; ctx.fillText("/ 100", 300, 430);
    if (analysisFrame?.width) { drawContain(ctx, analysisFrame, 500, 265, 500, 300); drawFootInset(ctx, analysisFrame, result.footFocus, 820, 385, 160); ctx.fillStyle="rgba(7,17,31,.82)";ctx.fillRect(520,492,268,50);ctx.fillStyle="#61e6d3";ctx.font='700 19px "Malgun Gothic", sans-serif';ctx.fillText(`AI 착지 프레임 · ${result.side}`,535,523); }
    ctx.font = '800 44px "Malgun Gothic", sans-serif'; ctx.fillStyle="#fff"; ctx.fillText(result.runnerType, 76, 625);
    [["착지 유형",result.strikeType,`분석 신뢰도 ${result.strikeConfidence}%`],["무릎 각도",`${result.averageKneeAngle}°`,"권장 범위 105~125°"],["상체 기울기",`${result.averageTrunkLean}°`,"권장 범위 6~14°"]].forEach(([label,value,detail],index)=>{const x=76+index*310;ctx.fillStyle="rgba(255,255,255,.09)";ctx.fillRect(x,690,280,170);ctx.fillStyle="#9fb3c8";ctx.font='600 24px "Malgun Gothic", sans-serif';ctx.fillText(label,x+24,735);ctx.fillStyle="#fff";ctx.font='800 36px "Malgun Gothic", sans-serif';ctx.fillText(value,x+24,790);ctx.fillStyle="#9fb3c8";ctx.font='600 18px "Malgun Gothic", sans-serif';ctx.fillText(detail,x+24,827)});
    ctx.fillStyle="#fff";ctx.font='800 34px "Malgun Gothic", sans-serif';ctx.fillText("순금이 코치의 한마디",76,950);drawApprovalStamp(ctx,742,900);ctx.fillStyle="#d8e5ee";ctx.font='600 29px "Malgun Gothic", sans-serif';
    const words=(result.improvements[0]||"지금 자세 좋아. 이 리듬을 유지하면서 편안하게 달려봐.").split(" ");let line="",y=1010;words.forEach(word=>{const test=`${line}${word} `;if(ctx.measureText(test).width>900){ctx.fillText(line,76,y);line=`${word} `;y+=42}else line=test});ctx.fillText(line,76,y);
    ctx.fillStyle="rgba(97,230,211,.13)";ctx.beginPath();ctx.roundRect(76,1120,900,54,18);ctx.fill();ctx.fillStyle="#9df3e5";ctx.font='700 21px "Malgun Gothic", sans-serif';ctx.fillText(nextScoreTip(result),100,1155);
    ctx.fillStyle="#d8e5ee";ctx.font='600 22px "Malgun Gothic", sans-serif';ctx.fillText("※ 촬영 각도·속도·조명에 따라 결과가 달라질 수 있으며 의료 진단이 아닙니다.",76,1205);
    ctx.fillStyle="#61e6d3";ctx.font="700 25px Arial";ctx.fillText("PROJECT FREEDOM AI · AI-assisted estimate",76,1270);return card;
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
    button.textContent = "순금이 코치가 영상을 보고 있어요…";
    document.dispatchEvent(new CustomEvent("sungeum:state", { detail: { state: "working" } }));
    showCoachProgress("영상 형식과 촬영 조건을 확인하는 중이에요.", 8);
    try {
      const response = await fetch("/running-form/preflight", { method: "POST", body: new FormData(form) });
      const preflight = await response.json();
      if (!response.ok || !preflight.ok) throw new Error(preflight.error || "영상을 확인하지 못했어요.");
      showCoachProgress("AI 코치가 관절 위치를 찾을 준비를 하고 있어요.", 20);
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
      status.innerHTML = `<div class="alert alert-success"><strong>🐾 순금이 AI 러닝코치 분석 완료</strong><br>실제 영상 프레임을 바탕으로 코칭 결과를 정리했어요.</div>
        <div class="row g-2">
          <div class="col-6"><div class="run-check" data-status="pass"><small>러닝폼 종합 점수</small><br><strong>${result.score}점</strong></div></div>
          <div class="col-6"><div class="run-check" data-status="pass"><small>러너 유형</small><br><strong>${escapeHtml(result.runnerType)}</strong></div></div>
          <div class="col-6"><div class="run-check"><small>착지 유형</small><br><strong>${result.strikeType}</strong><br><small>신뢰도 ${result.strikeConfidence}%</small></div></div>
          <div class="col-6"><div class="run-check"><small>평균 무릎 각도</small><br><strong>${result.averageKneeAngle}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>평균 상체 기울기</small><br><strong>${result.averageTrunkLean}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>관절 추출 성공률</small><br><strong>${result.detectionRate}%</strong></div></div>
        </div><div class="run-result-section mt-3"><strong>👏 순금이가 찾은 잘한 점</strong><ul class="mt-2 mb-0">${strengths}</ul></div><div class="run-result-section mt-3"><strong>🎯 다음 러닝에서 바꿀 한 가지</strong><ul class="mt-2 mb-0">${improvements}</ul></div><div id="runShareArea" class="mt-3"><h3 class="h5 fw-bold">순금이 코치의 SNS 공유 결과지</h3></div><div class="small text-secondary mt-3">AI 영상 기반 참고 분석이며 의료 진단이 아닙니다. 촬영 각도·속도·조명에 따라 판정이 달라질 수 있어요.</div>`;
      const card = await makeShareCard(result, canvas), shareArea = document.getElementById("runShareArea"); shareArea.appendChild(card);
      const download = document.createElement("button"); download.type="button"; download.className="btn btn-success w-100 fw-bold"; download.textContent="SNS 결과 이미지 저장"; download.onclick=()=>{const link=document.createElement("a");link.download="sungeum-running-form-result.png";link.href=card.toDataURL("image/png");link.click()};shareArea.appendChild(download);
      const saveState=document.createElement("div");saveState.className="small text-secondary mt-2";saveState.textContent="생성 기록에 저장하는 중…";shareArea.appendChild(saveState);
      try{const saved=await saveRunningHistory(result,card);saveState.innerHTML=`✓ 생성 기록에 저장했어요 · <a href="/history">기록 보기</a>`;saveState.dataset.historyId=saved.history_id}catch(saveError){saveState.textContent=`결과는 완성됐지만 생성 기록 저장에 실패했어요: ${friendlyError(saveError)}`}
    } catch (error) {
      document.dispatchEvent(new CustomEvent("sungeum:state", { detail: { state: "failed", duration: 1800 } }));
      status.className = "alert alert-danger mt-4"; status.textContent = friendlyError(error);
    } finally {
      button.textContent = "순금이에게 분석 맡기기 · 3크레딧"; sync();
    }
  });
})();
