const MEDIAPIPE_VERSION = "0.10.21";
const WASM_ROOT = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/wasm`;
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

const CONNECTIONS = [
  [11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],
  [23,25],[25,27],[27,29],[29,31],[24,26],[26,28],[28,30],[30,32]
];
const LEFT = { shoulder: 11, hip: 23, knee: 25, ankle: 27, heel: 29, toe: 31 };
const RIGHT = { shoulder: 12, hip: 24, knee: 26, ankle: 28, heel: 30, toe: 32 };

let landmarkerPromise;
let lastVideoTimestamp = 0;

async function createLandmarker() {
  if (!landmarkerPromise) {
    landmarkerPromise = import(`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/+esm`)
      .then(async ({ FilesetResolver, PoseLandmarker }) => {
        const vision = await FilesetResolver.forVisionTasks(WASM_ROOT);
        return PoseLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
          runningMode: "VIDEO",
          numPoses: 1,
          minPoseDetectionConfidence: 0.55,
          minPosePresenceConfidence: 0.55,
          minTrackingConfidence: 0.55,
        });
      });
  }
  return landmarkerPromise;
}

function angle(a, b, c) {
  const ab = { x: a.x - b.x, y: a.y - b.y };
  const cb = { x: c.x - b.x, y: c.y - b.y };
  const dot = ab.x * cb.x + ab.y * cb.y;
  const size = Math.hypot(ab.x, ab.y) * Math.hypot(cb.x, cb.y);
  if (!size) return null;
  return Math.acos(Math.max(-1, Math.min(1, dot / size))) * 180 / Math.PI;
}

function visible(landmark) {
  return landmark && (landmark.visibility ?? 1) >= 0.55;
}

function selectSide(landmarks) {
  const score = side => Object.values(side).reduce((sum, index) => sum + (landmarks[index]?.visibility ?? 0), 0);
  return score(LEFT) >= score(RIGHT) ? { name: "왼쪽 측면", points: LEFT } : { name: "오른쪽 측면", points: RIGHT };
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function evaluateForm(detectionRate, knee, trunk, footSamples) {
  const contacts = [...footSamples].sort((a, b) => b.ankleY - a.ankleY).slice(0, Math.max(3, Math.ceil(footSamples.length * .3)));
  const footDelta = contacts.length ? median(contacts.map(item => item.toeY - item.heelY)) : 0;
  const strikeType = footDelta > .012 ? "포어풋형" : footDelta < -.012 ? "리어풋형" : "미드풋형";
  const strikeConfidence = Math.min(95, Math.max(55, Math.round(58 + Math.abs(footDelta) * 900 + contacts.length)));
  const trunkPoints = Math.max(8, 25 - Math.abs(trunk - 9) * 1.5);
  const kneePoints = Math.max(8, 25 - Math.abs(knee - 115) * .55);
  const score = Math.round(Math.max(55, Math.min(96, detectionRate * .3 + trunkPoints + kneePoints + (strikeType === "미드풋형" ? 20 : 16))));
  const runnerType = trunk > 16 ? `${strikeType} · 전방 추진형` : trunk < 6 ? `${strikeType} · 안정 중심형` : `${strikeType} · 균형 추진형`;
  const strengths = [], improvements = [];
  if (detectionRate >= 85) strengths.push("측면 자세가 선명해 관절 움직임을 안정적으로 추적했어요.");
  if (trunk >= 6 && trunk <= 14) strengths.push("상체 기울기가 자연스러운 추진 범위에 있어요.");
  else if (trunk > 14) improvements.push("허리를 굽히기보다 발목부터 몸 전체를 살짝 기울여 보세요.");
  else improvements.push("상체가 다소 세워져 있어 발목에서 아주 조금 전방으로 기울여 보세요.");
  if (knee >= 95 && knee <= 135) strengths.push("무릎 굴곡이 충격 흡수와 추진을 함께 만들 수 있는 범위예요.");
  else improvements.push("보폭을 조금 줄이고 발이 몸 아래에 닿게 연습해 보세요.");
  if (strikeType === "리어풋형") improvements.push("뒤꿈치가 몸보다 멀리 앞서 닿지 않는지 확인하고 케이던스를 3~5%만 높여 보세요.");
  else if (strikeType === "포어풋형") improvements.push("종아리에 부담이 몰리지 않도록 뒤꿈치가 자연스럽게 내려오는지 확인해 보세요.");
  else strengths.push("발바닥 중앙에 가까운 착지 패턴이 감지됐어요.");
  return { score, strikeType, strikeConfidence, runnerType, strengths: strengths.slice(0, 3), improvements: improvements.slice(0, 3) };
}

function drawPose(canvas, video, landmarks) {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  ctx.lineWidth = Math.max(3, canvas.width / 220);
  ctx.strokeStyle = "#55f2d3";
  ctx.fillStyle = "#ffcc4d";
  for (const [start, end] of CONNECTIONS) {
    const a = landmarks[start], b = landmarks[end];
    if (!visible(a) || !visible(b)) continue;
    ctx.beginPath(); ctx.moveTo(a.x * canvas.width, a.y * canvas.height);
    ctx.lineTo(b.x * canvas.width, b.y * canvas.height); ctx.stroke();
  }
  landmarks.forEach(point => {
    if (!visible(point)) return;
    ctx.beginPath(); ctx.arc(point.x * canvas.width, point.y * canvas.height, ctx.lineWidth * 1.2, 0, Math.PI * 2); ctx.fill();
  });
}

function seek(video, time) {
  return new Promise((resolve, reject) => {
    const done = () => { cleanup(); resolve(); };
    const failed = () => { cleanup(); reject(new Error("영상 프레임을 읽지 못했어요.")); };
    const cleanup = () => { video.removeEventListener("seeked", done); video.removeEventListener("error", failed); };
    video.addEventListener("seeked", done, { once: true });
    video.addEventListener("error", failed, { once: true });
    video.currentTime = Math.min(time, Math.max(0, video.duration - 0.01));
  });
}

export async function analyzePose(video, canvas, onProgress = () => {}) {
  if (!video.duration || !video.videoWidth) throw new Error("영상 미리보기가 준비된 뒤 다시 시도해 주세요.");
  const landmarker = await createLandmarker();
  const duration = Math.min(video.duration, 12);
  const sampleCount = Math.max(12, Math.min(60, Math.round(duration * 6)));
  const samples = [];
  let best = null;
  let bestQuality = -1;
  let bestFootFocus = null;
  // MediaPipe VIDEO mode requires timestamps to keep increasing even when the
  // user analyzes the same video again in the same browser tab.
  const timestampBase = Math.max(lastVideoTimestamp + 1, Math.ceil(performance.now()));

  for (let index = 0; index < sampleCount; index += 1) {
    const time = sampleCount === 1 ? 0 : (duration * index / (sampleCount - 1));
    await seek(video, time);
    const timestamp = timestampBase + index;
    lastVideoTimestamp = timestamp;
    const result = landmarker.detectForVideo(video, timestamp);
    const landmarks = result.landmarks?.[0];
    if (landmarks) {
      const side = selectSide(landmarks);
      const p = side.points;
      if ([p.shoulder,p.hip,p.knee,p.ankle].every(i => visible(landmarks[i]))) {
        const knee = angle(landmarks[p.hip], landmarks[p.knee], landmarks[p.ankle]);
        const shoulder = landmarks[p.shoulder], hip = landmarks[p.hip];
        const trunk = Math.abs(Math.atan2(shoulder.x - hip.x, hip.y - shoulder.y) * 180 / Math.PI);
        samples.push({ knee, trunk, side: side.name });
        if ([p.heel, p.toe].every(i => visible(landmarks[i]))) {
          samples[samples.length - 1].foot = { ankleY: landmarks[p.ankle].y, heelY: landmarks[p.heel].y, toeY: landmarks[p.toe].y };
        }
      }
      const selected = selectSide(landmarks);
      const selectedPoints = selected.points;
      const bodyIndexes = [0, selectedPoints.shoulder, selectedPoints.hip, selectedPoints.knee, selectedPoints.ankle, selectedPoints.heel, selectedPoints.toe];
      const bodyVisibility = bodyIndexes.reduce((sum, pointIndex) => sum + (landmarks[pointIndex]?.visibility ?? 0), 0);
      const footVisible = [selectedPoints.ankle, selectedPoints.heel, selectedPoints.toe].every(pointIndex => visible(landmarks[pointIndex]));
      const inFrame = bodyIndexes.every(pointIndex => {
        const point = landmarks[pointIndex];
        return point && point.x >= .015 && point.x <= .985 && point.y >= .015 && point.y <= .985;
      });
      // Prefer a complete side view, then the moment the visible ankle is
      // closest to the ground. This makes the evidence frame match a strike analysis.
      const contactBonus = footVisible ? landmarks[selectedPoints.ankle].y * 12 : 0;
      const quality = bodyVisibility + (footVisible ? 18 : 0) + (inFrame ? 24 : 0) + contactBonus;
      if (quality > bestQuality) {
        bestQuality = quality;
        best = landmarks;
        bestFootFocus = footVisible ? {
          x: (landmarks[selectedPoints.ankle].x + landmarks[selectedPoints.heel].x + landmarks[selectedPoints.toe].x) / 3,
          y: (landmarks[selectedPoints.ankle].y + landmarks[selectedPoints.heel].y + landmarks[selectedPoints.toe].y) / 3,
        } : null;
        drawPose(canvas, video, landmarks);
      }
    }
    onProgress(Math.round((index + 1) / sampleCount * 100));
  }

  if (!samples.length || !best) throw new Error("전신 관절을 안정적으로 찾지 못했어요. 정확한 측면으로 다시 촬영해 주세요.");
  const average = key => samples.reduce((sum, item) => sum + item[key], 0) / samples.length;
  const averageKneeAngle = Math.round(average("knee"));
  const averageTrunkLean = Math.round(average("trunk") * 10) / 10;
  const evaluation = evaluateForm(Math.round(samples.length / sampleCount * 100), averageKneeAngle, averageTrunkLean, samples.map(item => item.foot).filter(Boolean));
  return {
    detectionRate: Math.round(samples.length / sampleCount * 100),
    side: samples[0].side,
    averageKneeAngle,
    averageTrunkLean,
    sampledFrames: sampleCount,
    footFocus: bestFootFocus,
    ...evaluation,
  };
}
