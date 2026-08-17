(() => {
  "use strict";
  const W = 1080, H = 1350;
  const $ = id => document.getElementById(id);
  const val = id => ($(id)?.value || "").trim();
  let backgroundImage = null;

  const themes = [
    { name: "포커스형", accent: "#ffbf58", panel: "rgba(13,18,31,.90)", ink: "#ffffff", muted: "#d9e0eb", layout: "bottom" },
    { name: "에디토리얼형", accent: "#ef5b45", panel: "rgba(255,248,239,.94)", ink: "#291b18", muted: "#5f514c", layout: "top" },
    { name: "프리미엄형", accent: "#72e9b6", panel: "rgba(13,55,52,.89)", ink: "#ffffff", muted: "#d8efea", layout: "full" },
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

    let panelX = 58, panelY = 600, panelW = 964, panelH = 690;
    if (theme.layout === "top") { panelY = 58; panelH = 690; }
    if (theme.layout === "full") { panelX = 0; panelY = 0; panelW = W; panelH = H; }
    rounded(ctx, panelX, panelY, panelW, panelH, theme.layout === "full" ? 0 : 42, theme.panel);

    const x = theme.layout === "full" ? 88 : 98;
    const contentWidth = theme.layout === "full" ? 904 : 884;
    let y = theme.layout === "top" ? 110 : theme.layout === "full" ? 280 : 650;
    ctx.textBaseline = "top";
    ctx.fillStyle = theme.accent;
    ctx.font = '800 32px "Noto Sans KR", "Malgun Gothic", sans-serif';
    ctx.fillText(val("posterCompany") || "업체명", x, y); y += 74;

    const title = val("posterHeadline") || "광고 제목을 입력하세요";
    const titleSize = fitFont(ctx, title, contentWidth, 3, 70, 42);
    ctx.font = `800 ${titleSize}px "Noto Sans KR", "Malgun Gothic", sans-serif`;
    ctx.fillStyle = theme.ink;
    y = drawLines(ctx, title, x, y, contentWidth, Math.round(titleSize * 1.24), 3) + 24;

    const benefit = val("posterBenefit");
    if (benefit) {
      ctx.font = '500 31px "Noto Sans KR", "Malgun Gothic", sans-serif';
      ctx.fillStyle = theme.muted;
      y = drawLines(ctx, benefit, x, y, contentWidth, 47, 3) + 30;
    }

    const offer = val("posterOffer");
    if (offer) {
      ctx.font = '800 31px "Noto Sans KR", "Malgun Gothic", sans-serif';
      const offerWidth = Math.min(contentWidth, Math.max(430, ctx.measureText(offer).width + 80));
      rounded(ctx, x, y, offerWidth, 82, 23, theme.accent);
      ctx.fillStyle = "#171922"; ctx.fillText(offer, x + 36, y + 21); y += 112;
    }

    ctx.font = '700 27px "Noto Sans KR", "Malgun Gothic", sans-serif';
    ctx.fillStyle = theme.ink;
    drawLines(ctx, val("posterContact"), x, Math.min(y, H - 125), contentWidth, 38, 2);
    ctx.fillStyle = theme.accent; ctx.fillRect(x, H - 52, 170, 7);
  }

  function render(image = backgroundImage) {
    const root = $("posterResults"); root.innerHTML = "";
    themes.forEach((theme, index) => {
      const card = document.createElement("div"); card.className = "card p-2";
      const canvas = document.createElement("canvas"); canvas.className = "poster-preview";
      draw(canvas, theme, image);
      const button = document.createElement("button"); button.className = "btn btn-outline-light mt-2";
      button.textContent = `${theme.name} PNG 저장`;
      button.onclick = () => { const link = document.createElement("a"); link.download = `poster-${index + 1}.png`; link.href = canvas.toDataURL("image/png"); link.click(); };
      card.append(canvas, button); root.append(card);
    });
  }

  function usePhoto() {
    const file = $("posterPhoto").files[0]; if (!file) return render();
    const image = new Image(); image.onload = () => { backgroundImage = image; render(); };
    image.src = URL.createObjectURL(file);
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
    const response = await fetch("/poster/background", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: val("aiBackgroundPrompt") }) });
    const data = await response.json(); if (!response.ok) { status.textContent = data.error || "생성 실패"; return; }
    const image = new Image(); image.onload = () => { backgroundImage = image; render(); status.textContent = "글자 없는 AI 배경이 적용됐습니다."; }; image.src = data.image_url;
  }

  const examples = { posterCompany: ["오늘의커피", "튼튼정형외과", "런바디 스튜디오"], posterHeadline: ["한 모금으로 만나는 여름", "통증 없는 일상으로", "오늘 시작하는 건강한 변화"], posterBenefit: ["신선한 재료로 완성한 시그니처 메뉴", "꼼꼼한 상담과 맞춤 진료", "초보자도 편안한 맞춤 코칭"], posterOffer: ["신메뉴 출시 기념 할인", "첫 방문 상담 혜택", "체험 수업 신청하기"], posterContact: ["네이버 예약 또는 매장 문의", "카카오톡으로 문의하세요", "프로필 링크에서 예약하세요"] };
  function rotateExamples() { Object.entries(examples).forEach(([id, list]) => { const input = $(id); if (input && !input.value && document.activeElement !== input) input.placeholder = `예: ${list[Math.floor(Math.random() * list.length)]}`; }); }

  document.addEventListener("DOMContentLoaded", () => {
    $("makePosters").onclick = usePhoto; $("suggestPoster").onclick = suggest; $("makeAiBackground").onclick = createBackground;
    ["posterCompany", "posterHeadline", "posterBenefit", "posterOffer", "posterContact"].forEach(id => $(id).addEventListener("input", () => render()));
    rotateExamples(); setInterval(rotateExamples, 4000); render();
  });
})();
