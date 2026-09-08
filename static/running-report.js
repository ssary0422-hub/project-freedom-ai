/* Shared preview, download and history image. All measurements come from the analyzer. */
window.createRunningReport = async function (result, frame, copy = {}) {
  await document.fonts.ready;
  const card = document.createElement('canvas');
  card.width = 1080;
  card.className = 'run-share-card';
  card.setAttribute('role', 'img');
  card.setAttribute('aria-label', copy.share_title || '러닝폼 분석 리포트');
  const ctx = card.getContext('2d');
  const ink = '#191b1d', muted = '#737e88', rule = '#e3e6e9', accent = '#5369e8';
  const font = (size, weight = 500) => `${weight} ${size}px "Noto Sans KR", "Malgun Gothic", sans-serif`;
  function text(value, x, y, size = 26, color = ink, weight = 500, maxWidth) {
    ctx.font = font(size, weight);
    // Fit short labels without clipping localized values or long runner types.
    while (maxWidth && ctx.measureText(String(value)).width > maxWidth && size > 16) ctx.font = font(--size, weight);
    ctx.fillStyle = color;
    ctx.fillText(String(value ?? '—'), x, y);
  }
  function lines(value, width, size) {
    ctx.font = font(size);
    const output = [];
    for (const paragraph of String(value || '').split('\n')) {
      let line = '';
      for (const char of paragraph) {
        if (line && ctx.measureText(line + char).width > width) { output.push(line.trim()); line = ''; }
        line += char;
      }
      output.push(line.trim());
    }
    return output;
  }
  const note = lines(result.improvements?.[0] || copy.next_goal || '같은 조건에서 다시 촬영해 자세 변화를 비교해보세요.', 872, 28);
  const disclaimer = lines(copy.disclaimer || 'AI 영상 기반 참고 분석이며 의료 진단이 아닙니다. 촬영 조건에 따라 결과가 달라질 수 있어요.', 936, 20);
  const noteHeight = Math.max(134, 54 + note.length * 42);
  const footerY = 1080 + noteHeight + 34;
  card.height = Math.max(1350, footerY + disclaimer.length * 30 + 58);
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, card.width, card.height);
  function line(y) { ctx.fillStyle = rule; ctx.fillRect(72, y, 936, 1); }
  function panel(x, y, w, h, fill = '#f7f8fa') {
    ctx.fillStyle = fill; ctx.beginPath(); ctx.roundRect(x, y, w, h, 8); ctx.fill();
  }
  text('순금이의', 72, 60, 19, muted);
  text('AI 작업실', 72, 98, 32, ink, 700);
  const wordmarkEnd = 72 + ctx.measureText('AI 작업실').width;
  ctx.fillStyle = accent; ctx.beginPath(); ctx.arc(wordmarkEnd + 12, 94, 4, 0, Math.PI * 2); ctx.fill();
  text(copy.report_meta || 'RUNNING / FORM REPORT', 666, 85, 20, muted, 500, 342);
  line(130);
  text(copy.report_title || (document.documentElement.lang === 'ko' ? '나의 러닝폼 리포트' : copy.title || 'My running form report'), 72, 216, 52, ink, 700, 936);
  text(copy.metric_score || '러닝폼 종합 점수', 72, 276, 23, muted);
  text(result.score, 66, 390, 112, ink, 700);
  text('/ 100', 300, 386, 30, muted);
  text(copy.metric_runner || '러너 유형', 464, 298, 23, muted);
  text(result.runnerType, 464, 347, 34, ink, 600, 544);
  text(copy.report_estimate || 'AI-assisted estimate', 464, 384, 20, muted, 500, 544);
  line(419);
  text(copy.landing_frame || 'AI 착지 분석 장면', 72, 463, 24, ink, 600);
  const hasFrame = frame && frame.width > 0 && frame.height > 0;
  const hasFocus = hasFrame && Number.isFinite(result.footFocus?.x) && Number.isFinite(result.footFocus?.y);
  const imageWidth = hasFocus ? 642 : 936;
  panel(72, 488, imageWidth, 330);
  if (hasFrame) {
    const scale = Math.min(imageWidth / frame.width, 330 / frame.height);
    ctx.drawImage(frame, 72 + (imageWidth - frame.width * scale) / 2, 488 + (330 - frame.height * scale) / 2, frame.width * scale, frame.height * scale);
    if (hasFocus) {
      const crop = Math.min(frame.width, frame.height) * .34;
      const sx = Math.max(0, Math.min(frame.width - crop, result.footFocus.x * frame.width - crop / 2));
      const sy = Math.max(0, Math.min(frame.height - crop, result.footFocus.y * frame.height - crop * .62));
      panel(738, 488, 270, 330);
      ctx.drawImage(frame, sx, sy, crop, crop, 748, 498, 250, 250);
      text(copy.foot_zoom || '착지 확대', 758, 791, 22, muted, 500, 230);
    }
  } else text(copy.frame_unavailable || '분석 장면을 불러오지 못했어요.', 100, 658, 27, muted, 500, 880);
  const metrics = [
    [copy.metric_strike || '착지 유형', result.strikeType, `${copy.metric_confidence || '분석 신뢰도'} ${result.strikeConfidence}%`],
    [copy.metric_knee || '평균 무릎 각도', `${result.averageKneeAngle}°`, copy.range_knee || 'AI 참고 범위 105–125°'],
    [copy.metric_trunk || '평균 상체 기울기', `${result.averageTrunkLean}°`, copy.range_trunk || 'AI 참고 범위 6–14°']
  ];
  metrics.forEach(([label, value, detail], index) => {
    const x = 72 + index * 320;
    panel(x, 847, 296, 163);
    text(label, x + 22, 887, 22, muted, 500, 252);
    text(value, x + 22, 939, 36, ink, 650, 252);
    text(detail, x + 22, 981, 19, muted, 500, 252);
  });
  text(copy.coach || '순금이의 코칭 한마디', 72, 1056, 27, ink, 600);
  panel(72, 1080, 936, noteHeight, '#f6f6fc');
  ctx.fillStyle = accent; ctx.fillRect(72, 1097, 3, noteHeight - 34);
  note.forEach((row, index) => text(row, 104, 1130 + index * 42, 28));
  disclaimer.forEach((row, index) => text(row, 72, footerY + index * 30, 20, muted));
  line(card.height - 76);
  text('PROJECT FREEDOM AI', 72, card.height - 34, 18, muted);
  text('projectfreedom-ai.com', 741, card.height - 34, 18, muted, 500, 267);
  return card;
};
