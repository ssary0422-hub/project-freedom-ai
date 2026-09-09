/* Local SRT inspection. No uploads, storage or automatic timing changes. */
(function (root) {
  'use strict';
  const stamp = s => {
    const m = /^(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})$/.exec(s);
    if (!m) throw Error('시간은 00:00:01,000 형식이어야 합니다.');
    return (+m[1] * 3600 + +m[2] * 60 + +m[3]) * 1000 + +m[4];
  };
  function parse(source) {
    if (source.length > 500000) throw Error('50만 자 이하의 SRT 파일을 사용해주세요.');
    const blocks = source.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n').trim().split(/\n[ \t]*\n/);
    if (!source.trim()) throw Error('SRT 파일을 선택하거나 자막을 붙여넣어주세요.');
    return blocks.map((block, i) => {
      const lines = block.split('\n');
      if (!/^\d+$/.test(lines[0].trim())) throw Error(`${i + 1}번째 블록의 자막 번호를 확인해주세요.`);
      const time = /^\s*(\S+)\s+-->\s+(\S+)\s*$/.exec(lines[1] || '');
      if (!time || !lines.slice(2).join('').trim()) throw Error(`${i + 1}번째 블록의 시간과 본문을 확인해주세요. 위치 설정이 있는 확장 SRT는 지원하지 않습니다.`);
      const start = stamp(time[1]), end = stamp(time[2]);
      if (end <= start) throw Error(`${i + 1}번째 자막의 종료 시간이 시작 시간보다 늦어야 합니다.`);
      return {start, end, text: lines.slice(2).join('\n'), time: `${time[1].replace('.', ',')} --> ${time[2].replace('.', ',')}`};
    });
  }
  const plain = s => s.replace(/<[^>]*>/g, '');
  const count = s => Array.from(plain(s).replace(/\s/g, '')).length;
  function inspect(cues, width, speed) {
    const issues = [];
    let furthest = -1, furthestIndex = -1;
    cues.forEach((cue, i) => {
      const notes = [];
      if (i && cue.start < cues[i - 1].start) notes.push('시작 시간 순서가 뒤바뀜');
      if (cue.start < furthest) notes.push(`${furthestIndex + 1}번 자막과 시간 겹침`);
      if (cue.end > furthest) { furthest = cue.end; furthestIndex = i; }
      if (cue.text.split('\n').some(line => count(line) > width)) notes.push(`한 줄 ${width}자 초과`);
      if (cue.text.split('\n').length > 2) notes.push('3줄 이상');
      if (count(cue.text) / ((cue.end - cue.start) / 1000) > speed) notes.push(`초당 ${speed}자 초과`);
      if (notes.length) issues.push({index: i + 1, notes});
    });
    return issues;
  }
  function wrap(text, width) {
    // Preserve styled captions exactly; splitting tags can damage formatting.
    if (/<[^>]*>/.test(text)) return text;
    const chars = Array.from(text.replace(/\n/g, ' ').trim()), lines = [];
    while (chars.length > width) {
      let cut = chars.slice(0, width + 1).lastIndexOf(' ');
      if (cut < Math.floor(width / 2)) cut = width;
      lines.push(chars.splice(0, cut).join('').trim());
      while (chars[0] === ' ') chars.shift();
    }
    if (chars.length) lines.push(chars.join(''));
    return lines.join('\n');
  }
  function serialize(cues, width) {
    return cues.map((cue, i) => `${i + 1}\n${cue.time}\n${width ? wrap(cue.text, width) : cue.text}`).join('\n\n') + '\n';
  }
  const api = {parse, inspect, serialize};
  if (typeof module !== 'undefined') module.exports = api;
  else root.SubtitleCheck = api;
})(typeof window !== 'undefined' ? window : globalThis);
