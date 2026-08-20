const MEDIAPIPE_VERSION = "0.10.21";
const WASM_ROOT = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/wasm`;
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

const CONNECTIONS = [
  [11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],
  [23,25],[25,27],[27,29],[29,31],[24,26],[26,28],[28,30],[30,32]
];
const LEFT = { shoulder: 11, hip: 23, knee: 25, ankle: 27 };
const RIGHT = { shoulder: 12, hip: 24, knee: 26, ankle: 28 };

let landmarkerPromise;

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

  for (let index = 0; index < sampleCount; index += 1) {
    const time = sampleCount === 1 ? 0 : (duration * index / (sampleCount - 1));
    await seek(video, time);
    const result = landmarker.detectForVideo(video, Math.round(time * 1000) + index);
    const landmarks = result.landmarks?.[0];
    if (landmarks) {
      const side = selectSide(landmarks);
      const p = side.points;
      if ([p.shoulder,p.hip,p.knee,p.ankle].every(i => visible(landmarks[i]))) {
        const knee = angle(landmarks[p.hip], landmarks[p.knee], landmarks[p.ankle]);
        const shoulder = landmarks[p.shoulder], hip = landmarks[p.hip];
        const trunk = Math.abs(Math.atan2(shoulder.x - hip.x, hip.y - shoulder.y) * 180 / Math.PI);
        samples.push({ knee, trunk, side: side.name });
      }
      best = landmarks;
      drawPose(canvas, video, landmarks);
    }
    onProgress(Math.round((index + 1) / sampleCount * 100));
  }

  if (!samples.length || !best) throw new Error("전신 관절을 안정적으로 찾지 못했어요. 정확한 측면으로 다시 촬영해 주세요.");
  const average = key => samples.reduce((sum, item) => sum + item[key], 0) / samples.length;
  return {
    detectionRate: Math.round(samples.length / sampleCount * 100),
    side: samples[0].side,
    averageKneeAngle: Math.round(average("knee")),
    averageTrunkLean: Math.round(average("trunk") * 10) / 10,
    sampledFrames: sampleCount,
  };
}
