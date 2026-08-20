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
      status.className = "mt-4";
      status.innerHTML = `<div class="alert alert-success"><strong>🐾 자세 추출 AI 검사 완료</strong><br>실제 영상 프레임에서 관절을 찾았어요.</div>
        <div class="row g-2">
          <div class="col-6"><div class="run-check" data-status="pass"><small>관절 추출 성공률</small><br><strong>${result.detectionRate}%</strong></div></div>
          <div class="col-6"><div class="run-check" data-status="pass"><small>인식 방향</small><br><strong>${result.side}</strong></div></div>
          <div class="col-6"><div class="run-check"><small>평균 무릎 각도</small><br><strong>${result.averageKneeAngle}°</strong></div></div>
          <div class="col-6"><div class="run-check"><small>평균 상체 기울기</small><br><strong>${result.averageTrunkLean}°</strong></div></div>
        </div><div class="small text-secondary mt-3">현재는 관절 추출 기술검증 단계예요. 착지·점수·러너 유형은 다음 분석 엔진에서 연결됩니다.</div>`;
    } catch (error) {
      status.className = "alert alert-danger mt-4"; status.textContent = error.message;
    } finally {
      button.textContent = "순금이에게 분석 맡기기"; sync();
    }
  });
})();

