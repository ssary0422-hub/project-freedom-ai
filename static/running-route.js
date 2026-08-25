(() => {
  const state = { purpose: 'easy', style: 'park', condition: 'good', time: 'day' };
  const distanceSelect = document.getElementById('route-distance');
  const customDistance = document.getElementById('route-custom-distance');
  const button = document.getElementById('route-location');
  const status = document.getElementById('route-status');
  const result = document.getElementById('route-result');
  if (!distanceSelect || !button || !result) return;
  distanceSelect.addEventListener('change', () => {
    customDistance.hidden = distanceSelect.value !== 'custom';
    if (distanceSelect.value === 'custom') customDistance.focus();
  });
  document.querySelectorAll('.route-options').forEach((group) => {
    group.querySelectorAll('button').forEach((item) => item.addEventListener('click', () => {
      group.querySelectorAll('button').forEach((other) => other.classList.remove('selected'));
      item.classList.add('selected');
      state[group.dataset.field] = item.dataset.value;
    }));
  });
  const purposeLabels = { easy: '가볍게 달리기', fitness: '체력 키우기', recovery: '회복 러닝', record: '기록 도전' };
  const styleLabels = { park: '공원·산책로', flat: '평지 위주', quiet: '조용한 길', hill: '오르막 포함' };
  const mascot = '/static/brand/sungeum-running-coach-goggles-v1-transparent.png';

  function renderRoute(position) {
    const selected = distanceSelect.value === 'custom' ? customDistance.value : distanceSelect.value;
    const km = Math.max(1, Math.min(100, Number(selected) || 5));
    const pace = state.condition === 'tired' ? 8 : state.purpose === 'record' ? 5.5 : state.purpose === 'recovery' ? 7.5 : 6.5;
    const minutes = Math.round(km * pace);
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    result.hidden = false;
    result.innerHTML = `<h2>오늘의 추천 코스</h2><div class="route-summary"><div class="route-stat"><strong>${km.toFixed(1)}km</strong><span>목표 거리</span></div><div class="route-stat"><strong>${minutes}분</strong><span>예상 시간</span></div><div class="route-stat"><strong>${styleLabels[state.style]}</strong><span>코스 스타일</span></div></div><div id="route-map" class="route-map"></div><p><strong>${purposeLabels[state.purpose]}</strong> 목적과 컨디션을 반영해 현재 위치를 출발지로 표시했어. 아래 3가지 코스 중 하나를 골라 달려보자.</p><div class="route-alternatives"><div class="route-alternative"><strong>안정형</strong> · ${km.toFixed(1)}km 왕복 · ${styleLabels[state.style]} 중심</div><div class="route-alternative"><strong>균형형</strong> · ${(km * 1.05).toFixed(1)}km 순환 · ${state.condition === 'tired' ? '평지와 휴식 지점 우선' : '적당한 자극 포함'}</div><div class="route-alternative"><strong>도전형</strong> · ${(km * 1.1).toFixed(1)}km · ${state.purpose === 'record' ? '기록 도전 구간 포함' : '마지막 1km 페이스업'}</div></div><p class="small text-muted">지도는 현재 위치와 코스 반경 미리보기야. 실제 도로 경로와 통행 가능 여부는 출발 전에 확인해줘.</p><div class="route-tip"><img src="${mascot}" alt="순금이"><span>처음 5분은 천천히. 오늘 목표는 완주하고 기분 좋게 돌아오는 거야 🐾</span></div>`;
    if (window.L) {
      const map = L.map('route-map').setView([lat, lon], 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
      L.marker([lat, lon]).addTo(map).bindPopup('현재 출발 위치').openPopup();
      const radius = Math.max(0.01, km / 2 / 111);
      const points = [];
      for (let i = 0; i <= 24; i += 1) {
        const angle = (i / 24) * Math.PI * 2;
        points.push([lat + Math.sin(angle) * radius, lon + Math.cos(angle) * radius / Math.max(0.2, Math.cos(lat * Math.PI / 180))]);
      }
      L.polyline(points, { color: '#377dff', weight: 5, opacity: 0.82 }).addTo(map);
      L.circle([lat, lon], { radius: radius * 111000, color: '#61e6d3', fillOpacity: 0.08 }).addTo(map);
      map.fitBounds(L.latLngBounds(points).pad(0.12));
    }
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
    status.textContent = '추천 완료!';
    button.disabled = false;
  }

  button.addEventListener('click', () => {
    if (!navigator.geolocation) { status.textContent = '이 브라우저에서는 위치 기능을 사용할 수 없어.'; return; }
    button.disabled = true;
    status.textContent = '현재 위치를 확인하고 순금이가 코스를 고르는 중이야…';
    navigator.geolocation.getCurrentPosition(renderRoute, (error) => {
      status.textContent = error.code === 1 ? '위치 권한이 거부됐어. 주소창의 위치 권한을 허용한 뒤 다시 눌러줘.' : '현재 위치를 확인하지 못했어. 잠시 후 다시 시도해줘.';
      button.disabled = false;
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  });
})();
