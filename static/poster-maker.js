(() => {
  "use strict";
  const W = 1080, H = 1350;
  const $ = id => document.getElementById(id);
  const val = id => ($(id)?.value || "").trim();
  let subjectImage = null, backgroundImage = null, logoImage = null, currentThemeIndex = 0;
  let hasUserResult = false;
  let serverApproved = false;
  let suggestedCopySets = [];

  const assistantBrief = new URLSearchParams(window.location.search).get("assistant_brief");
  if (assistantBrief && $("posterPurpose")) $("posterPurpose").value = assistantBrief;

  function setButtonBusy(button, busy, busyLabel) {
    if (!button) return;
    if (busy) button.dataset.originalLabel = button.textContent;
    button.disabled = busy;
    button.textContent = busy ? busyLabel : (button.dataset.originalLabel || button.textContent);
  }

  const themes = [
    { name: "순금 추천 · 브랜드 에디토리얼형", layout: "editorial", accent: "#ffc85c", ink: "#fff", muted: "#d9ddea" },
    { name: "사진 중심 · 정보 패널형", layout: "left", accent: "#63dcff", ink: "#fff", muted: "#d5e2ed" },
    { name: "하단 집중 · 프로모션형", layout: "bottom", accent: "#ffca62", ink: "#fff", muted: "#f0e2d5" },
  ];

  function rounded(ctx, x, y, w, h, radius, color) {
    ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(x, y, w, h, radius); ctx.fill();
  }

  function cover(ctx, image) {
    const scale = Math.max(W / image.width, H / image.height);
    const sw = W / scale, sh = H / scale;
    ctx.drawImage(image, (image.width - sw) / 2, (image.height - sh) / 2, sw, sh, 0, 0, W, H);
  }

  function contain(ctx, image, x, y, w, h) {
    const scale = Math.min(w / image.width, h / image.height);
    const dw = image.width * scale, dh = image.height * scale;
    ctx.drawImage(image, x + (w - dw) / 2, y + h - dh, dw, dh);
  }

  function rawLines(ctx, text, maxWidth) {
    const lines = []; let current = "";
    const tokens = text.includes(" ") ? text.split(/(\s+)/).filter(Boolean) : [...text];
    for (const token of tokens) {
      const candidate = current + token;
      if (current.trim() && ctx.measureText(candidate.trimEnd()).width > maxWidth) {
        lines.push(current.trim()); current = token.trimStart();
      } else current = candidate;
    }
    if (current.trim()) lines.push(current.trim());
    return lines;
  }

  function fitFont(ctx, text, maxWidth, maxLines, start, minimum) {
    for (let size = start; size >= minimum; size -= 2) {
      ctx.font = `800 ${size}px "Noto Sans KR", "Malgun Gothic", sans-serif`;
      if (rawLines(ctx, text, maxWidth).length <= maxLines) return size;
    }
    return minimum;
  }

  function drawLines(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
    const lines = rawLines(ctx, text, maxWidth).slice(0, maxLines);
    lines.forEach((line, index) => ctx.fillText(line, x, y + index * lineHeight));
    return y + lines.length * lineHeight;
  }

  function drawLogo(ctx, image) {
    if (!image) return;
    const scale = Math.min(300 / image.width, 112 / image.height, 1);
    const w = image.width * scale, h = image.height * scale;
    rounded(ctx, W - w - 76, 54, w + 28, h + 22, 14, "rgba(255,255,255,.94)");
    ctx.drawImage(image, W - w - 62, 65, w, h);
  }

  function drawQualitySeal(ctx, accent) {
    ctx.save(); ctx.translate(907, 1210); ctx.rotate(-0.06);
    ctx.strokeStyle = accent; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(0, 0, 86, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(0, 0, 73, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = accent;
    ctx.beginPath(); ctx.ellipse(0, -4, 24, 20, 0, 0, Math.PI * 2); ctx.fill();
    [[-30, -31, 10, 14, -.35], [-10, -43, 10, 14, -.12], [12, -43, 10, 14, .12], [31, -30, 10, 14, .35]].forEach(([x, y, rx, ry, rotation]) => {
      ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rotation, 0, Math.PI * 2); ctx.fill();
    });
    ctx.textAlign = "center"; ctx.font = '900 18px "Malgun Gothic", sans-serif';
    ctx.fillText("순금 검수", 0, 27); ctx.fillText("완료", 0, 50);
    ctx.restore(); ctx.textAlign = "left";
  }

  function qualityCheck(ctx, theme) {
    const issues = [];
    const required = [["posterCompany", "업체명"], ["posterHeadline", "광고 제목"], ["posterBenefit", "핵심 혜택"], ["posterContact", "연락처·예약 방법"]];
    required.forEach(([id, label]) => { if (!val(id)) issues.push(`${label}을 입력하세요`); });
    const forbidden = /직접 입력|미정|없음|TODO|example/i;
    ["posterCompany", "posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach(id => {
      if (forbidden.test(val(id))) issues.push("임시 문구를 실제 내용으로 바꾸세요");
    });
    const headlineWidth = theme.layout === "editorial" ? 590 : (theme.layout === "left" ? 526 : 900);
    ctx.font = `800 ${fitFont(ctx, val("posterHeadline"), headlineWidth, 3, theme.layout === "editorial" ? 82 : 58, 38)}px "Malgun Gothic", sans-serif`;
    if (rawLines(ctx, val("posterHeadline"), headlineWidth).length > 3) issues.push("제목이 너무 깁니다");
    ctx.font = '600 28px "Malgun Gothic", sans-serif';
    if (rawLines(ctx, val("posterBenefit"), theme.layout === "editorial" ? 530 : 900).length > 4) issues.push("핵심 혜택이 너무 깁니다");
    return [...new Set(issues)];
  }

  function drawEditorial(ctx, theme, approved) {
    const bg = ctx.createLinearGradient(0, 0, W, H);
    bg.addColorStop(0, "#090d1d"); bg.addColorStop(.55, "#17132a"); bg.addColorStop(1, "#34213d");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "rgba(255,200,92,.13)"; ctx.beginPath(); ctx.arc(910, 280, 330, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "rgba(103,220,255,.08)"; ctx.beginPath(); ctx.arc(160, 1120, 370, 0, Math.PI * 2); ctx.fill();
    if (backgroundImage) { ctx.save(); ctx.globalAlpha = .38; cover(ctx, backgroundImage); ctx.restore(); ctx.fillStyle = "rgba(5,8,20,.6)"; ctx.fillRect(0, 0, W, H); }

    ctx.textBaseline = "top";
    ctx.fillStyle = theme.accent; ctx.font = '800 25px "Malgun Gothic", sans-serif';
    ctx.fillText((val("posterCompany") || "BRAND").toUpperCase(), 66, 62);
    const offer = val("posterOffer");
    if (offer) {
      ctx.font = '800 22px "Malgun Gothic", sans-serif'; const width = Math.min(350, ctx.measureText(offer).width + 54);
      rounded(ctx, W - width - 64, 52, width, 58, 29, theme.accent); ctx.fillStyle = "#17131f"; ctx.fillText(offer, W - width - 37, 68);
    }

    const title = val("posterHeadline") || "광고 제목을 입력하세요";
    const titleSize = fitFont(ctx, title, 600, 3, 82, 52);
    ctx.font = `900 ${titleSize}px "Malgun Gothic", sans-serif`; ctx.fillStyle = theme.ink;
    const titleBottom = drawLines(ctx, title, 64, 165, 600, Math.round(titleSize * 1.14), 3);
    ctx.fillStyle = theme.accent; ctx.fillRect(66, titleBottom + 14, 170, 7);

    if (subjectImage) contain(ctx, subjectImage, 525, 310, 540, 720);
    else {
      ctx.fillStyle = "rgba(255,255,255,.045)"; ctx.beginPath(); ctx.arc(825, 650, 250, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,.36)"; ctx.font = '700 25px "Malgun Gothic", sans-serif'; ctx.textAlign = "center";
      ctx.fillText("제품·업체 사진을 넣으면", 825, 620); ctx.fillText("이 영역에 크게 배치됩니다", 825, 660); ctx.textAlign = "left";
    }

    rounded(ctx, 64, 610, 525, 350, 32, "rgba(10,15,31,.9)");
    ctx.fillStyle = theme.accent; ctx.font = '900 22px "Malgun Gothic", sans-serif'; ctx.fillText("WHY THIS BRAND", 102, 652);
    ctx.fillStyle = theme.muted; ctx.font = '600 29px "Malgun Gothic", sans-serif';
    drawLines(ctx, val("posterBenefit") || "핵심 혜택을 입력하면 고객이 읽기 쉽게 정리됩니다", 102, 708, 450, 48, 4);

    rounded(ctx, 64, 1004, 950, 210, 30, "rgba(255,255,255,.08)");
    ctx.fillStyle = "#fff"; ctx.font = '900 27px "Malgun Gothic", sans-serif'; ctx.fillText("지금 바로 확인하세요", 104, 1046);
    ctx.fillStyle = theme.muted; ctx.font = '700 28px "Malgun Gothic", sans-serif';
    drawLines(ctx, val("posterContact") || "연락처·예약 방법", 104, 1094, 650, 42, 2);
    drawLogo(ctx, logoImage);
  }

  function drawClassic(ctx, theme, approved) {
    const gradient = ctx.createLinearGradient(0, 0, W, H); gradient.addColorStop(0, "#19243d"); gradient.addColorStop(1, "#684873");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, W, H);
    if (subjectImage) cover(ctx, subjectImage); else if (backgroundImage) cover(ctx, backgroundImage);
    ctx.fillStyle = "rgba(0,0,0,.42)"; ctx.fillRect(0, 0, W, H);
    const bottom = theme.layout === "bottom"; const x = 48, y = bottom ? 720 : 52, w = bottom ? 984 : 610, h = bottom ? 578 : 700;
    rounded(ctx, x, y, w, h, 36, "rgba(6,15,28,.91)");
    const tx = x + 42, tw = w - 84; let ty = y + 44; ctx.textBaseline = "top";
    ctx.fillStyle = theme.accent; ctx.font = '800 25px "Malgun Gothic", sans-serif'; ctx.fillText(val("posterCompany") || "업체명", tx, ty); ty += 62;
    const title = val("posterHeadline") || "광고 제목을 입력하세요"; const size = fitFont(ctx, title, tw, 3, bottom ? 58 : 62, 38);
    ctx.fillStyle = theme.ink; ctx.font = `900 ${size}px "Malgun Gothic", sans-serif`; ty = drawLines(ctx, title, tx, ty, tw, size * 1.18, 3) + 25;
    ctx.fillStyle = theme.accent; ctx.fillRect(tx, ty, 180, 5); ty += 28;
    ctx.fillStyle = theme.muted; ctx.font = '600 27px "Malgun Gothic", sans-serif'; ty = drawLines(ctx, val("posterBenefit"), tx, ty, tw, 42, 4) + 24;
    if (val("posterOffer")) { rounded(ctx, tx, ty, Math.min(tw, 450), 62, 16, theme.accent); ctx.fillStyle = "#101923"; ctx.font = '800 23px "Malgun Gothic", sans-serif'; ctx.fillText(val("posterOffer"), tx + 24, ty + 17); ty += 82; }
    ctx.fillStyle = theme.ink; ctx.font = '700 24px "Malgun Gothic", sans-serif'; drawLines(ctx, val("posterContact"), tx, Math.min(ty, y + h - 70), tw, 38, 2);
    drawLogo(ctx, logoImage);
  }

  function draw(canvas, theme) {
    canvas.width = W; canvas.height = H; const ctx = canvas.getContext("2d");
    const issues = qualityCheck(ctx, theme); const locallyReady = hasUserResult && issues.length === 0;
    if (theme.layout === "editorial") drawEditorial(ctx, theme, false); else drawClassic(ctx, theme, false);
    if ($("posterWatermark")?.checked) { ctx.fillStyle = theme.muted; ctx.font = '500 18px Arial'; ctx.fillText("PROJECT FREEDOM AI", 64, H - 54); }
    return { approved: locallyReady && serverApproved, locallyReady, issues };
  }

  function makeQualityStatus(result) {
    const stamp = document.createElement("div"); stamp.className = `sungeum-quality-stamp mb-3${result.approved ? "" : " is-pending"}`; stamp.setAttribute("role", "status");
    stamp.innerHTML = `<svg class="sungeum-paw" viewBox="0 0 64 64" aria-hidden="true"><ellipse cx="32" cy="39" rx="17" ry="15"/><ellipse cx="14" cy="25" rx="7" ry="9"/><ellipse cx="27" cy="16" rx="7" ry="9"/><ellipse cx="40" cy="16" rx="7" ry="9"/><ellipse cx="52" cy="26" rx="7" ry="9"/></svg><span><strong>${result.approved ? "순금 검수 완료" : "최종 검수 전"}</strong><small>${result.approved ? "서버 90점 출고 기준을 통과했어요" : (result.issues[0] || "완성 후 서버 검수를 진행합니다")}</small></span>`;
    return stamp;
  }

  function render() {
    const root = $("posterResults"); root.innerHTML = ""; const theme = themes[currentThemeIndex];
    const card = document.createElement("div"); card.className = "card p-3";
    const canvas = document.createElement("canvas"); canvas.className = "poster-preview"; const result = draw(canvas, theme);
    const label = document.createElement("div"); label.className = "fw-bold mb-2"; label.textContent = theme.name;
    const controls = document.createElement("div"); controls.className = "d-grid gap-2 mt-3";
    const download = document.createElement("button"); download.className = "btn btn-primary"; download.textContent = "이 포스터 PNG 저장";
    download.disabled = !result.approved; download.title = result.approved ? "" : "순금 검수를 먼저 통과하세요";
    download.onclick = () => { const link = document.createElement("a"); link.download = "sungeum-approved-poster.png"; link.href = canvas.toDataURL("image/png"); link.click(); };
    const alternate = document.createElement("button"); alternate.className = "btn btn-outline-primary"; alternate.textContent = "다른 무료 글자 배치 보기";
    alternate.onclick = () => { currentThemeIndex = (currentThemeIndex + 1) % themes.length; render(); };
    controls.append(download, alternate); card.append(makeQualityStatus(result), label, canvas, controls); root.append(card);
  }

  function normalizeLogo(image) {
    const sample = document.createElement("canvas"), maxSide = 1200;
    const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
    sample.width = Math.max(1, Math.round(image.width * scale)); sample.height = Math.max(1, Math.round(image.height * scale));
    const ctx = sample.getContext("2d", {willReadFrequently: true}); ctx.drawImage(image, 0, 0, sample.width, sample.height);
    const data = ctx.getImageData(0, 0, sample.width, sample.height), px = data.data;
    const corners = [[0,0],[sample.width-1,0],[0,sample.height-1],[sample.width-1,sample.height-1]];
    const bg = [0,1,2].map(channel => Math.round(corners.reduce((sum,[x,y]) => sum + px[(y*sample.width+x)*4+channel], 0) / corners.length));
    let minX=sample.width,minY=sample.height,maxX=-1,maxY=-1, changed=0;
    for (let y=0;y<sample.height;y+=1) for(let x=0;x<sample.width;x+=1) {
      const i=(y*sample.width+x)*4, distance=Math.max(Math.abs(px[i]-bg[0]),Math.abs(px[i+1]-bg[1]),Math.abs(px[i+2]-bg[2]));
      if (distance > 24 && px[i+3] > 20) { minX=Math.min(minX,x); minY=Math.min(minY,y); maxX=Math.max(maxX,x); maxY=Math.max(maxY,y); changed+=1; }
    }
    if (maxX < 0 || changed < sample.width*sample.height*.001) return image;
    const pad=Math.max(4,Math.round(Math.max(maxX-minX,maxY-minY)*.04)); minX=Math.max(0,minX-pad);minY=Math.max(0,minY-pad);maxX=Math.min(sample.width-1,maxX+pad);maxY=Math.min(sample.height-1,maxY+pad);
    const out=document.createElement("canvas");out.width=maxX-minX+1;out.height=maxY-minY+1;const outCtx=out.getContext("2d");outCtx.drawImage(sample,minX,minY,out.width,out.height,0,0,out.width,out.height);
    const outData=outCtx.getImageData(0,0,out.width,out.height), outPx=outData.data;
    for(let i=0;i<outPx.length;i+=4){const d=Math.max(Math.abs(outPx[i]-bg[0]),Math.abs(outPx[i+1]-bg[1]),Math.abs(outPx[i+2]-bg[2]));if(d<18)outPx[i+3]=0;else if(d<34)outPx[i+3]=Math.round(outPx[i+3]*(d-18)/16);}
    outCtx.putImageData(outData,0,0); return out;
  }

  function loadFile(file, setter, {logo=false} = {}) { if (!file) return; const image = new Image(); image.onload = () => { setter(logo ? normalizeLogo(image) : image); serverApproved = false; render(); URL.revokeObjectURL(image.src); }; image.src = URL.createObjectURL(file); }
  function usePhoto() {
    hasUserResult = true; serverApproved = false; loadFile($("posterPhoto").files[0], image => { subjectImage = image; }); loadFile($("posterLogo").files[0], image => { logoImage = image; }, {logo:true}); render();
  }

  function applyCopySet(set) {
    ["posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach((id, i) => $(id).value = set[i]);
    hasUserResult = true;
    serverApproved = false;
    render();
  }

  async function suggest({ autoApply = false } = {}) {
    const root = $("copyChoices"); root.textContent = "추천 중…";
    try {
      const response = await fetch("/poster/suggest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ business: val("posterCompany"), purpose: val("posterPurpose") }) });
      const data = await response.json(); if (!response.ok) throw new Error(data.error || "문구 추천 실패"); root.innerHTML = "";
      suggestedCopySets = data.sets || [];
      data.sets.forEach((set, index) => { const button = document.createElement("button"); button.type = "button"; button.className = "btn btn-outline-primary text-start"; button.textContent = `${index + 1}. ${set[0]} · ${set[2]}`; button.onclick = () => applyCopySet(set); root.append(button); });
      if (autoApply && data.sets[0]) applyCopySet(data.sets[0]);
      return true;
    } catch (error) { root.textContent = error.message; return false; }
  }

  async function createBackground() {
    const status = $("posterStatus"); status.textContent = "AI 배경 생성 중…";
    try {
      const response = await fetch("/poster/background", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ business: val("posterCompany"), purpose: val("posterPurpose"), style: val("posterImageStyle"), prompt: val("aiBackgroundPrompt") }) });
      const data = await response.json(); if (!response.ok) throw new Error(data.error || "배경 생성 실패");
      await new Promise((resolve, reject) => { const image = new Image(); image.onload = () => { backgroundImage = image; hasUserResult = true; render(); resolve(); }; image.onerror = () => reject(new Error("생성된 배경 이미지를 불러오지 못했습니다.")); image.src = `${data.image_url}?v=${Date.now()}`; });
      status.textContent = data.fallback ? "안전한 프리미엄 대체 배경이 자동 적용됐습니다." : "글자 없는 AI 배경이 적용됐습니다.";
      return true;
    } catch (error) { status.textContent = error.message; return false; }
  }

  async function savePosterHistory(canvas) {
    const response = await fetch("/poster/history", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({company:val("posterCompany"),headline:val("posterHeadline"),benefit:val("posterBenefit"),offer:val("posterOffer"),contact:val("posterContact"),image:canvas.toDataURL("image/png")})});
    const saved = await response.json();
    if (!response.ok || !saved.ok) throw new Error(saved.error || "생성 기록 저장에 실패했어요.");
    return saved;
  }

  async function verifyPosterQuality(canvas) {
    const response = await fetch("/poster/quality", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        company: val("posterCompany"),
        purpose: val("posterPurpose"),
        image: canvas.toDataURL("image/png")
      })
    });
    const review = await response.json();
    if (!response.ok) throw new Error(review.error || "포스터 품질 검수에 실패했어요.");
    return review;
  }

  async function findApprovedPoster() {
    let best = {score: 0, issues: []};
    const candidates = suggestedCopySets.length ? suggestedCopySets : [[val("posterHeadline"), val("posterBenefit"), val("posterOffer"), val("posterContact")]];
    for (const copySet of candidates) {
      applyCopySet(copySet);
      for (let index = 0; index < themes.length; index += 1) {
        const canvas = document.createElement("canvas");
        const localResult = draw(canvas, themes[index]);
        if (!localResult.locallyReady) continue;
        const review = await verifyPosterQuality(canvas);
        if (review.score > best.score) best = review;
        if (review.approved && review.score >= 90) {
          currentThemeIndex = index;
          serverApproved = true;
          render();
          return review;
        }
      }
    }
    throw new Error(`90점 출고 기준을 통과하지 못했어요. 최고 점수 ${best.score}점 · ${(best.issues || [])[0] || "다른 사진이나 더 구체적인 혜택이 필요해요."}`);
  }

  async function makeOneClick() {
    const button = $("makeOneClickPoster"), status = $("posterMainStatus");
    if (!val("posterCompany") || !val("posterPurpose")) { status.className = "poster-main-status text-danger mb-3"; status.textContent = "업체명과 홍보 내용을 먼저 입력해주세요."; return; }
    const startedAt = Date.now();
    let currentStep = "1/2 광고 문구를 구성하고 있습니다.";
    const showProgress = () => {
      const seconds = Math.floor((Date.now() - startedAt) / 1000), minutes = Math.floor(seconds / 60), rest = seconds % 60;
      const elapsed = minutes ? `${minutes}분 ${rest}초` : `${rest}초`;
      status.textContent = `${currentStep} · 경과 ${elapsed}${seconds >= 120 ? " · 정상적으로 계속 작업 중이에요. 화면을 닫지 마세요." : ""}`;
    };
    setButtonBusy(button, true, "⏳ 순금이가 문구를 만들고 있어요…"); status.className = "poster-main-status text-primary mb-3"; showProgress();
    const progressTimer = setInterval(showProgress, 1000);
    try {
      if (!await suggest({ autoApply: true })) throw new Error("문구를 만들지 못했습니다. 다시 눌러주세요.");
      button.textContent = "🎨 AI 배경을 만들고 있어요…"; currentStep = "2/2 포스터 배경과 최종 배치를 만들고 있습니다."; showProgress();
      await createBackground();
      currentStep = "3/3 순금이가 완성 포스터를 검수하고 있어요."; showProgress();
      const review = await findApprovedPoster(); status.dataset.qualityScore = String(review.score);
      status.className = "poster-main-status text-success mb-3"; status.textContent = "포스터 완성! 생성 기록에 저장하고 있어요…";
      try { const saved=await savePosterHistory($("posterResults")?.querySelector("canvas")); status.innerHTML=`${review.score}점으로 완성! 생성 기록에도 저장했어요. <a href="/history">기록 보기</a>`; status.dataset.historyId=saved.history_id; }
      catch (saveError) { status.className="poster-main-status text-warning mb-3"; status.textContent=`90점 검수는 통과했지만 기록 저장에 실패했어요: ${saveError.message}`; }
      $("posterResults")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) { status.className = "poster-main-status text-danger mb-3"; status.textContent = error.message; }
    finally { clearInterval(progressTimer); setButtonBusy(button, false); }
  }

  const examples = { posterCompany: ["윤슬도자기", "달빛책방", "모모식물상점"], posterHeadline: ["손끝에서 시작되는 나만의 그릇", "금요일 밤, 작가와 책 사이", "우리 집 식물에게 새 화분을"], posterBenefit: ["처음이어도 편안한 소규모 원데이 클래스", "열두 명만 함께하는 깊이 있는 북토크", "흙과 화분이 모두 준비된 분갈이 수업"], posterOffer: ["이번 주말 클래스 모집", "선착순 12명 예약", "재료비 포함 신청"], posterContact: ["프로필 링크에서 신청하세요", "DM으로 예약해주세요", "온라인 예약 또는 매장 문의"] };
  function rotateExamples() { Object.entries(examples).forEach(([id, list]) => { const input = $(id); if (input && !input.value && document.activeElement !== input) input.placeholder = `예: ${list[Math.floor(Math.random() * list.length)]}`; }); }

  document.addEventListener("DOMContentLoaded", () => {
    $("makePosters").onclick = usePhoto; $("suggestPoster").onclick = () => suggest(); $("makeAiBackground").onclick = createBackground; $("makeOneClickPoster").onclick = makeOneClick;
    $("posterPhoto").addEventListener("change", usePhoto); $("posterLogo").addEventListener("change", usePhoto); $("posterWatermark").addEventListener("change", render);
    ["posterCompany", "posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach(id => $(id).addEventListener("input", () => { hasUserResult = true; serverApproved = false; render(); }));
    rotateExamples(); setInterval(rotateExamples, 4000); render();
  });
})();
