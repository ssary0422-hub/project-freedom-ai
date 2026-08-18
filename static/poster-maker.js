(() => {
  "use strict";
  const W = 1080, H = 1350;
  const $ = id => document.getElementById(id);
  const val = id => ($(id)?.value || "").trim();
  let backgroundImage = null, logoImage = null;
  let currentThemeIndex = 0;

  const themes = [
    { name: "AI 추천 · 사진 중심형", accent: "#63dcff", panel: "rgba(4,18,31,.92)", ink: "#ffffff", muted: "#d5e2ed", layout: "left", label: "" },
    { name: "무료 배치 · 하단 정보형", accent: "#ffca62", panel: "rgba(16,18,25,.91)", ink: "#ffffff", muted: "#f0e2d5", layout: "bottom", label: "" },
    { name: "무료 배치 · 미니멀형", accent: "#8be1bd", panel: "rgba(5,30,31,.84)", ink: "#ffffff", muted: "#d5ebe4", layout: "minimal", label: "" },
  ];

  function rounded(ctx, x, y, w, h, radius, color) {
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.roundRect(x, y, w, h, radius); ctx.fill();
  }

  function cover(ctx, image) {
    const scale = Math.max(W / image.width, H / image.height);
    const sw = W / scale, sh = H / scale;
    ctx.drawImage(image, (image.width - sw) / 2, (image.height - sh) / 2, sw, sh, 0, 0, W, H);
  }

  function drawLogo(ctx, image) {
    if (!image) return;
    const maxW = 190, maxH = 82;
    const scale = Math.min(maxW / image.width, maxH / image.height, 1);
    const w = image.width * scale, h = image.height * scale;
    rounded(ctx, W - w - 80, 62, w + 28, h + 22, 14, "rgba(255,255,255,.92)");
    ctx.drawImage(image, W - w - 66, 73, w, h);
  }

  function linesFor(ctx, text, maxWidth, maxLines) {
    const lines = []; let current = "";
    for (const character of [...text]) {
      const candidate = current + character;
      if (current && ctx.measureText(candidate).width > maxWidth) { lines.push(current); current = character; }
      else current = candidate;
    }
    if (current) lines.push(current);
    if (lines.length > maxLines) {
      const clipped = lines.slice(0, maxLines);
      clipped[maxLines - 1] = clipped[maxLines - 1].replace(/.$/, "…");
      return clipped;
    }
    return lines;
  }

  function fitFont(ctx, text, maxWidth, maxLines, start, minimum) {
    for (let size = start; size >= minimum; size -= 2) {
      ctx.font = `800 ${size}px "Noto Sans KR", "Malgun Gothic", sans-serif`;
      if (linesFor(ctx, text, maxWidth, maxLines).length <= maxLines &&
          linesFor(ctx, text, maxWidth, maxLines).every(line => ctx.measureText(line).width <= maxWidth)) return size;
    }
    return minimum;
  }

  function drawLines(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
    const lines = linesFor(ctx, text, maxWidth, maxLines);
    lines.forEach((line, index) => ctx.fillText(line, x, y + index * lineHeight));
    return y + lines.length * lineHeight;
  }

  function draw(canvas, theme, image) {
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, W, H);
    gradient.addColorStop(0, "#19243d"); gradient.addColorStop(1, "#684873");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, W, H);
    if (image) cover(ctx, image);

    const shade = ctx.createLinearGradient(0, 0, 0, H);
    shade.addColorStop(0, theme.layout === "top" ? "rgba(0,0,0,.26)" : "rgba(0,0,0,.04)");
    shade.addColorStop(.48, "rgba(0,0,0,.10)");
    shade.addColorStop(1, "rgba(0,0,0,.58)");
    ctx.fillStyle = shade; ctx.fillRect(0, 0, W, H);
    drawLogo(ctx, logoImage);

    let panelX = 48, panelY = 52, panelW = 570, panelH = 1246;
    if (theme.layout === "bottom") { panelX = 48; panelY = 720; panelW = 984; panelH = 578; }
    if (theme.layout === "minimal") { panelX = 48; panelY = 790; panelW = 984; panelH = 508; }
    rounded(ctx, panelX, panelY, panelW, panelH, 36, theme.panel);

    const x = panelX + 42;
    const contentWidth = panelW - 84;
    let y = panelY + 45;
    ctx.textBaseline = "top";
    ctx.letterSpacing = "0px";
    ctx.fillStyle = theme.accent;
    ctx.font = '700 25px "Noto Sans KR", "Malgun Gothic", sans-serif';
    ctx.fillText(val("posterCompany") || "업체명", x, y); y += 66;

    const title = val("posterHeadline") || "광고 제목을 입력하세요";
    const titleSize = fitFont(ctx, title, contentWidth, 2, theme.layout === "left" ? 58 : 52, 38);
    ctx.font = `800 ${titleSize}px "Noto Sans KR", "Malgun Gothic", sans-serif`;
    ctx.fillStyle = theme.ink;
    y = drawLines(ctx, title, x, y, contentWidth, Math.round(titleSize * 1.2), 2) + 24;

    ctx.fillStyle = theme.accent;
    ctx.fillRect(x, y, Math.min(260, contentWidth * .32), 4);
    y += 28;

    const benefit = val("posterBenefit");
    if (benefit) {
      ctx.font = '500 27px "Noto Sans KR", "Malgun Gothic", sans-serif';
      ctx.fillStyle = theme.muted;
      y = drawLines(ctx, benefit, x, y, contentWidth, 42, 2) + 28;
    }

    const offer = val("posterOffer");
    if (offer) {
      ctx.font = '800 25px "Noto Sans KR", "Malgun Gothic", sans-serif';
      const offerWidth = Math.min(contentWidth, Math.max(330, ctx.measureText(offer).width + 64));
      rounded(ctx, x, y, offerWidth, 70, 15, theme.accent);
      ctx.fillStyle = "#171922"; ctx.fillText(offer, x + 28, y + 19); y += 94;
    }

    ctx.font = '700 24px "Noto Sans KR", "Malgun Gothic", sans-serif';
    ctx.fillStyle = theme.ink;
    drawLines(ctx, val("posterContact"), x, Math.min(y, H - 125), contentWidth, 38, 2);
    ctx.fillStyle = theme.accent; ctx.fillRect(x, H - 52, 170, 7);
    if ($("posterWatermark")?.checked) {
      ctx.fillStyle = theme.muted;
      ctx.font = '500 18px Arial, sans-serif';
      ctx.fillText("PROJECT FREEDOM AI", W - 292, H - 60);
    }
  }

  function render(image = backgroundImage) {
    const root = $("posterResults"); root.innerHTML = "";
    const theme = themes[currentThemeIndex];
    const card = document.createElement("div"); card.className = "card p-3";
    const label = document.createElement("div"); label.className = "fw-bold mb-2"; label.textContent = theme.name;
    const canvas = document.createElement("canvas"); canvas.className = "poster-preview";
    draw(canvas, theme, image);
    const controls = document.createElement("div"); controls.className = "d-grid gap-2 mt-3";
    const download = document.createElement("button"); download.className = "btn btn-primary"; download.textContent = "이 포스터 PNG 저장";
    download.onclick = () => { const link = document.createElement("a"); link.download = "poster.png"; link.href = canvas.toDataURL("image/png"); link.click(); };
    const alternate = document.createElement("button"); alternate.className = "btn btn-outline-primary"; alternate.textContent = "다른 무료 글자 배치 보기";
    alternate.onclick = () => { currentThemeIndex = (currentThemeIndex + 1) % themes.length; render(image); };
    controls.append(download, alternate); card.append(label, canvas, controls); root.append(card);
  }

  function usePhoto() {
    const photo = $("posterPhoto").files[0];
    const logo = $("posterLogo").files[0];
    if (photo) { const image = new Image(); image.onload = () => { backgroundImage = image; render(); }; image.src = URL.createObjectURL(photo); }
    if (logo) { const image = new Image(); image.onload = () => { logoImage = image; render(); }; image.src = URL.createObjectURL(logo); }
    if (!photo && !logo) render();
  }

  async function suggest() {
    const root = $("copyChoices"); root.textContent = "추천 중…";
    const response = await fetch("/poster/suggest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ business: val("posterCompany"), purpose: val("posterPurpose") }) });
    const data = await response.json(); if (!response.ok) { root.textContent = data.error || "추천 실패"; return; }
    root.innerHTML = "";
    data.sets.forEach((set, index) => { const button = document.createElement("button"); button.type = "button"; button.className = "btn btn-outline-light text-start"; button.textContent = `${index + 1}. ${set[0]} · ${set[2]}`; button.onclick = () => { ["posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach((id, i) => $(id).value = set[i]); render(); }; root.append(button); });
  }

  async function createBackground() {
    const status = $("posterStatus"); status.textContent = "AI 배경 생성 중…";
    const response = await fetch("/poster/background", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ business: val("posterCompany"), purpose: val("posterPurpose"), style: val("posterImageStyle"), prompt: val("aiBackgroundPrompt") }) });
    const data = await response.json(); if (!response.ok) { status.textContent = data.error || "생성 실패"; return; }
    const image = new Image(); image.onload = () => { backgroundImage = image; render(); status.textContent = "글자 없는 AI 배경이 적용됐습니다."; }; image.src = data.image_url;
  }

  const examples = { posterCompany: ["오늘의커피", "튼튼정형외과", "런바디 스튜디오"], posterHeadline: ["한 모금으로 만나는 여름", "통증 없는 일상으로", "오늘 시작하는 건강한 변화"], posterBenefit: ["신선한 재료로 완성한 시그니처 메뉴", "꼼꼼한 상담과 맞춤 진료", "초보자도 편안한 맞춤 코칭"], posterOffer: ["신메뉴 출시 기념 할인", "첫 방문 상담 혜택", "체험 수업 신청하기"], posterContact: ["네이버 예약 또는 매장 문의", "카카오톡으로 문의하세요", "프로필 링크에서 예약하세요"] };
  function rotateExamples() { Object.entries(examples).forEach(([id, list]) => { const input = $(id); if (input && !input.value && document.activeElement !== input) input.placeholder = `예: ${list[Math.floor(Math.random() * list.length)]}`; }); }

  document.addEventListener("DOMContentLoaded", () => {
    $("makePosters").onclick = usePhoto; $("suggestPoster").onclick = suggest; $("makeAiBackground").onclick = createBackground;
    $("posterPhoto").addEventListener("change", usePhoto); $("posterLogo").addEventListener("change", usePhoto);
    $("posterWatermark").addEventListener("change", () => render());
    ["posterCompany", "posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach(id => $(id).addEventListener("input", () => render()));
    rotateExamples(); setInterval(rotateExamples, 4000); render();
  });
})();
