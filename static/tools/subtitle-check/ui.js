'use strict';
const $ = id => document.getElementById(id);
let cues = null;
function reset() { cues = null; $('wrap').disabled = $('download').disabled = true; $('preview').value = ''; $('issues').replaceChildren(); $('status').textContent = '입력 내용이 바뀌었습니다. 다시 검사해주세요.'; }
function settings() {
  if (!$('width').checkValidity() || !$('speed').checkValidity()) throw Error('한 줄 8~60자, 초당 3~40자 범위의 정수를 입력해주세요.');
  return [Number($('width').value), Number($('speed').value)];
}
function show(c, label) {
  const [width, speed] = settings(), issues = SubtitleCheck.inspect(c, width, speed);
  $('issues').replaceChildren();
  for (const issue of issues.slice(0, 200)) { const li = document.createElement('li'); li.textContent = `${issue.index}번 · ${issue.notes.join(' / ')}`; $('issues').append(li); }
  $('status').textContent = `${label}: 자막 ${c.length}개 중 확인할 자막 ${issues.length}개.${issues.length > 200 ? ' 목록은 처음 200개까지 표시합니다.' : ''}`;
}
$('source').addEventListener('input', () => { fileRequest++; reset(); });
for (const id of ['width', 'speed']) $(id).addEventListener('input', reset);
$('sample').onclick = () => { fileRequest++; $('source').value = '1\n00:00:00,000 --> 00:00:03,000\n오늘은 우리가 만든 영상의 자막이 얼마나 읽기 편한지 확인해볼게요.\n\n2\n00:00:02,500 --> 00:00:04,000\n앞 자막과 시간이 겹칩니다.\n'; reset(); $('source').focus(); };
let fileRequest = 0;
$('file').onchange = async () => {
  const request = ++fileRequest, file = $('file').files[0];
  reset(); $('source').value = '';
  if (!file) return;
  try {
    if (file.size > 1000000) throw Error('1 MB 이하의 SRT 파일을 사용해주세요.');
    const bytes = await file.arrayBuffer();
    if (request !== fileRequest) return;
    $('source').value = new TextDecoder('utf-8', {fatal: true}).decode(bytes);
    $('status').textContent = '파일을 읽었습니다. 자막 검사를 눌러주세요.';
  } catch (e) { if (request === fileRequest) $('status').textContent = e instanceof TypeError ? 'UTF-8 파일이 아닙니다. 편집기에서 UTF-8 SRT로 다시 저장해주세요.' : e.message; }
};
$('check').onclick = () => {
  reset();
  try { settings(); const parsed = SubtitleCheck.parse($('source').value); show(parsed, '검사 완료'); cues = parsed; $('preview').value = SubtitleCheck.serialize(cues); $('wrap').disabled = $('download').disabled = false; }
  catch (e) { $('status').textContent = e.message; }
};
$('wrap').onclick = () => {
  if (!cues) return;
  try { const output = SubtitleCheck.serialize(cues, settings()[0]); show(SubtitleCheck.parse(output), '줄바꿈 정리 후 재검사'); $('preview').value = output; }
  catch (e) { $('status').textContent = e.message; }
};
$('download').onclick = () => {
  if (!cues) return;
  const url = URL.createObjectURL(new Blob([$('preview').value], {type: 'text/plain;charset=utf-8'}));
  const a = document.createElement('a'); a.href = url; a.download = 'subtitles-reviewed.srt'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
