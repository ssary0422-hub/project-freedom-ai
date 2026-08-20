(() => {
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

  function drawCover(ctx, image, x, y, width, height) {
    const scale = Math.max(width / image.width, height / image.height), sourceWidth = width / scale, sourceHeight = height / scale;
    const sourceX = Math.max(0, (image.width - sourceWidth) / 2), sourceY = Math.max(0, (image.height - sourceHeight) / 2);
    ctx.save(); ctx.beginPath(); ctx.roundRect(x, y, width, height, 28); ctx.clip(); ctx.drawImage(image, sourceX, sourceY, sourceWidth, sourceHeight, x, y, width, height); ctx.restore();
  }

  function makeShareCard(result, analysisFrame) {
    const card = document.createElement("canvas"); card.width = 1080; card.height = 1350; card.className = "run-share-card";
    const ctx = card.getContext("2d"), gradient = ctx.createLinearGradient(0, 0, 1080, 1350);
    gradient.addColorStop(0, "#07111f"); gradient.addColorStop(.55, "#12344c"); gradient.addColorStop(1, "#0d766f"); ctx.fillStyle = gradient; ctx.fillRect(0, 0, 1080, 1350);
    ctx.fillStyle = "#61e6d3"; ctx.font = "800 30px Arial"; ctx.fillText("SUNGEUM AI RUNNING LAB", 76, 95);
    ctx.fillStyle = "#fff"; ctx.font = '900 70px "Malgun Gothic", sans-serif'; ctx.fillText("나의 러닝폼 분석", 76, 205);
    ctx.fillStyle = "#61e6d3"; ctx.font = "900 170px Arial"; ctx.fillText(String(result.score), 70, 440);
    ctx.fillStyle = "#fff"; ctx.font = "800 38px Arial"; ctx.fillText("/ 100", 300, 430);
    if (analysisFrame?.width) { drawCover(ctx, analysisFrame, 500, 265, 500, 300); ctx.fillStyle="rgba(7,17,31,.78)";ctx.fillRect(520,500,190,42);ctx.fillStyle="#61e6d3";ctx.font='700 21px "Malgun Gothic", sans-serif';ctx.fillText("AI 분석 프레임",535,528); }
    ctx.font = '800 44px "Malgun Gothic", sans-serif'; ctx.fillStyle="#fff"; ctx.fillText(result.runnerType, 76, 625);
    [["착지 유형",result.strikeType],["무릎 각도",`${result.averageKneeAngle}°`],["상체 기울기",`${result.averageTrunkLean}°`]].forEach(([label,value],index)=>{const x=76+index*310;ctx.fillStyle="rgba(255,255,255,.09)";ctx.fillRect(x,690,280,170);ctx.fillStyle="#9fb3c8";ctx.font='600 25px "Malgun Gothic", sans-serif';ctx.fillText(label,x+24,742);ctx.fillStyle="#fff";ctx.font='800 37px "Malgun Gothic", sans-serif';ctx.fillText(value,x+24,805)});
    ctx.fillStyle="#fff";ctx.font='800 34px "Malgun Gothic", sans-serif';ctx.fillText("순금이의 한마디",76,950);ctx.fillStyle="#d8e5ee";ctx.font='600 29px "Malgun Gothic", sans-serif';
    const words=(result.improvements[0]||"지금의 균형을 유지하며 편안하게 달려보세요.").split(" ");let line="",y=1010;words.forEach(word=>{const test=`${line}${word} `;if(ctx.measureText(test).width>900){ctx.fillText(line,76,y);line=`${word} `;y+=46}else line=test});ctx.fillText(line,76,y);
    ctx.fillStyle="#9fb3c8";ctx.font='500 20px "Malgun Gothic", sans-serif';ctx.fillText("촬영 각도·속도·조명에 따라 결과가 달라질 수 있으며 의료 진단이 아닙니다.",76,1205);
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
    button.textContent = "순금이가 영상을 확인하고 있어요…";
    status.className = "alert alert-info mt-4";
    status.textContent = "파일 형식과 촬영 조건을 확인하는 중입니다.";
    try {
      const response = await fetch("/running-form/preflight", { method: "POST", body: new FormData(form) });
      const preflight = await response.json();
      if (!response.ok || !preflight.ok) throw new Error(preflight.error || "영상을 확인하지 못했어요.");
      status.textContent = "자세 추출 AI를 불러오는 중이에요. 첫 분석은 모델 준비에 잠시 걸릴 수 있어요.";
      const { analyzePose } = await import("/static/running-pose-analyzer.js");
      canvas.classList.remove("d-none");
      const result = await analyzePose(preview, canvas, progress => {
        status.textContent = `순금이가 관절을 추적하고 있어요 · ${progress}%`;
      });
      const strengths = result.strengths.map(item => `<li>${escapeHtml(item)}</li>`).join("");
      const improvements = result.improvements.map(item => `<li>${escapeHtml(item)}</li>`).join("");
      status.className = "mt-4";
      status.innerHTML = `<div class="alert alert-success"><strong>🐾 순금이 러닝폼 분석 완료</strong><br>실제 영상 프레임을 바탕으로 결과를 정리했어요.</div>
        <div class="row g-2">
          <div class="col-6"><div class="run-check" data-status="pass"><small>러닝폼 종합 점수</small><br><strong>${result.score}점</strong></div></div>
          <div class="col-6"><div class="run-check" data-status="pass"><small>러너 유형</small><br><strong>${escapeHtml(result.runnerType)}</strong></div></div>
          <div class="col-6"><div class="run-check"><small>착지 유형</small><br><strong>${result.strikeType}</strong><br><small>신뢰도 ${result.strikeConfidence}%</small></div></div>
          <div class="col-6"><div class="run-check"><small>평균 무릎 각도</small><br><strong>${result.averageKneeAngle}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>평균 상체 기울기</small><br><strong>${result.averageTrunkLean}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>관절 추출 성공률</small><br><strong>${result.detectionRate}%</strong></div></div>
        </div><div class="run-result-section mt-3"><strong>좋았던 점</strong><ul class="mt-2 mb-0">${strengths}</ul></div><div class="run-result-section mt-3"><strong>개선하면 좋은 점</strong><ul class="mt-2 mb-0">${improvements}</ul></div><div id="runShareArea" class="mt-3"><h3 class="h5 fw-bold">SNS 공유 결과지</h3></div><div class="small text-secondary mt-3">AI 영상 기반 참고 분석이며 의료 진단이 아닙니다. 촬영 각도와 속도에 따라 판정이 달라질 수 있어요.</div>`;
      const card = makeShareCard(result, canvas), shareArea = document.getElementById("runShareArea"); shareArea.appendChild(card);
      const download = document.createElement("button"); download.type="button"; download.className="btn btn-success w-100 fw-bold"; download.textContent="SNS 결과 이미지 저장"; download.onclick=()=>{const link=document.createElement("a");link.download="sungeum-running-form-result.png";link.href=card.toDataURL("image/png");link.click()};shareArea.appendChild(download);
    } catch (error) {
      status.className = "alert alert-danger mt-4"; status.textContent = friendlyError(error);
    } finally {
      button.textContent = "순금이에게 분석 맡기기"; sync();
    }
  });
})();
