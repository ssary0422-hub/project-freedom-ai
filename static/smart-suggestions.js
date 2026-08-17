(() => {
  "use strict";

  const general = {
    moods: [
      "전문적이고 믿음직한 분위기", "따뜻하고 친근한 분위기", "젊고 활기찬 분위기",
      "차분하고 고급스러운 분위기", "정직하고 담백한 분위기", "트렌디하고 감각적인 분위기",
      "밝고 긍정적인 분위기", "편안하고 자연스러운 분위기", "세련되고 자신감 있는 분위기",
      "지역 고객에게 친근한 분위기", "프리미엄이지만 부담스럽지 않은 분위기", "활기차고 도전적인 분위기"
    ],
    images: [
      "밝은 자연광을 활용한 고급 실사 광고", "여백이 넉넉한 미니멀 브랜드 화보",
      "강렬한 색 대비의 SNS 광고 이미지", "실제 고객의 일상을 담은 자연스러운 사진",
      "제품과 서비스를 중심에 둔 스튜디오 촬영", "잡지 표지처럼 세련된 프리미엄 비주얼",
      "따뜻한 색감과 부드러운 그림자의 감성 사진", "브랜드 색상을 활용한 깔끔한 상업 광고",
      "시선을 끄는 역동적인 구도", "현실감 있고 신뢰를 주는 다큐멘터리 스타일",
      "입체적인 조명과 선명한 디테일", "모바일 화면에서 눈에 띄는 세로형 광고"
    ]
  };

  const industries = [
    { keys: ["병원", "의원", "정형외과", "피부과", "치과", "한의원", "클리닉"], moods: ["정확하고 체계적인 의료 전문 분위기", "환자를 안심시키는 따뜻한 분위기", "깨끗하고 현대적인 신뢰감", "지역 주민에게 친근한 진료 분위기", "차분하고 세심한 상담 분위기", "전문성과 배려가 함께 느껴지는 분위기"], images: ["밝고 청결한 진료 공간의 고급 실사", "전문 의료진 중심의 신뢰감 있는 광고", "자연광이 들어오는 편안한 상담 장면", "파란색과 흰색 중심의 미니멀 의료 광고", "정돈된 의료 장비와 깨끗한 공간", "환자의 불안을 낮추는 따뜻한 라이프스타일 사진"] },
    { keys: ["카페", "커피", "베이커리", "디저트"], moods: ["따뜻하고 여유로운 동네 카페 분위기", "감각적이고 트렌디한 분위기", "고소한 향이 느껴지는 편안한 분위기", "사진 찍고 싶은 세련된 분위기", "정성스럽고 수제 느낌이 나는 분위기", "조용히 머물고 싶은 아늑한 분위기"], images: ["아침 자연광과 따뜻한 커피의 감성 사진", "디저트 질감이 살아있는 클로즈업", "우드톤 카페 공간의 라이프스타일 화보", "메뉴가 돋보이는 미니멀 테이블 촬영", "SNS 피드에 어울리는 따뜻한 필름 색감", "김이 피어오르는 커피와 편안한 좌석 장면"] },
    { keys: ["헬스", "피트니스", "PT", "필라테스", "요가", "러닝"], moods: ["강렬하고 역동적인 분위기", "건강하고 자신감 넘치는 분위기", "꾸준한 변화를 응원하는 분위기", "전문 코칭이 느껴지는 분위기", "활기차고 긍정적인 커뮤니티 분위기", "집중력 있고 도전적인 분위기"], images: ["움직임과 땀이 느껴지는 역동적인 실사", "강한 명암의 프리미엄 스포츠 광고", "자세와 근육의 디테일이 선명한 촬영", "밝고 건강한 그룹 운동 장면", "새벽 러닝의 속도감 있는 시네마틱 사진", "깔끔한 운동 공간과 전문 코치 중심 구도"] },
    { keys: ["미용", "헤어", "네일", "뷰티", "화장품", "스킨케어"], moods: ["세련되고 감각적인 뷰티 분위기", "섬세하고 프리미엄한 분위기", "깨끗하고 투명한 분위기", "자신감을 높여주는 화려한 분위기", "편안한 셀프케어 분위기", "트렌드를 앞서가는 젊은 분위기"], images: ["부드러운 조명의 프리미엄 뷰티 화보", "피부와 제품 질감이 살아있는 클로즈업", "파스텔톤의 깨끗한 스튜디오 촬영", "글로시한 반사와 선명한 제품 광고", "감성적인 셀프케어 라이프스타일 사진", "SNS에서 눈에 띄는 컬러풀한 뷰티 비주얼"] },
    { keys: ["식당", "음식점", "고기", "치킨", "분식", "요리", "맛집"], moods: ["푸짐하고 정겨운 분위기", "신선하고 믿음직한 분위기", "활기차고 맛있는 분위기", "전통과 정성이 느껴지는 분위기", "깔끔하고 현대적인 다이닝 분위기", "가족과 함께하고 싶은 따뜻한 분위기"], images: ["갓 조리된 음식의 김과 윤기가 살아있는 사진", "재료의 신선함을 강조한 클로즈업", "따뜻한 식탁과 함께하는 사람들의 장면", "어두운 배경의 프리미엄 푸드 광고", "주방의 생동감이 느껴지는 실사", "SNS에서 군침 도는 선명한 메뉴 사진"] },
    { keys: ["부동산", "인테리어", "건축", "가구"], moods: ["전문적이고 신뢰감 있는 분위기", "안정적이고 품격 있는 분위기", "현대적이고 깔끔한 분위기", "생활을 이해하는 따뜻한 분위기", "정확하고 투명한 상담 분위기", "공간의 가치를 높이는 프리미엄 분위기"], images: ["넓은 공간감이 살아있는 밝은 실내 사진", "직선과 여백을 강조한 건축 화보", "따뜻한 조명의 편안한 주거 공간", "고급 소재와 디테일 중심의 클로즈업", "전문가의 상담 장면이 담긴 신뢰형 광고", "전후 변화가 명확한 인테리어 비주얼"] },
    { keys: ["교육", "학원", "과외", "영어", "수학", "공부"], moods: ["체계적이고 믿음직한 교육 분위기", "학생의 성장을 응원하는 분위기", "친근하고 질문하기 편한 분위기", "목표 달성에 집중하는 분위기", "밝고 창의적인 학습 분위기", "꼼꼼하고 책임감 있는 분위기"], images: ["집중해서 학습하는 밝은 교실 장면", "선생님과 학생의 자연스러운 소통", "성장과 성취를 상징하는 깔끔한 광고", "노트와 교재가 정돈된 감성 사진", "활기찬 토론과 참여형 수업 장면", "파란색 중심의 전문적인 교육 비주얼"] },
    { keys: ["여행", "호텔", "펜션", "숙박", "캠핑"], moods: ["설레고 자유로운 여행 분위기", "편안하고 여유로운 휴식 분위기", "특별한 경험을 주는 프리미엄 분위기", "자연과 가까운 힐링 분위기", "친구와 즐기는 활기찬 분위기", "로맨틱하고 감성적인 분위기"], images: ["탁 트인 풍경의 시네마틱 여행 사진", "따뜻한 노을과 편안한 숙소 장면", "여행자의 시점으로 담은 자연스러운 실사", "고급 호텔의 정돈된 객실 화보", "자연 속 휴식을 강조한 감성 사진", "모바일 세로 화면에 어울리는 역동적 여행 광고"] }
  ];

  const businessExamples = ["정형외과", "동네 카페", "프리미엄 헬스장", "피부관리실", "수제 베이커리", "영어 학원", "인테리어 스튜디오", "반려동물 병원", "한식 맛집", "여행 펜션"];
  const companyExamples = ["튼튼정형외과", "오늘의커피", "런바디 스튜디오", "온리유 스킨", "소담 베이커리", "브라이트 영어학원", "공간한줌", "우리동물병원", "담은식당", "숲속하루"];
  const topicTemplates = ["처음 방문하기 전 꼭 알아야 할 5가지", "고객들이 가장 자주 묻는 질문 7가지", "전문가가 알려주는 현명한 선택 방법", "비용보다 먼저 확인해야 할 핵심 포인트", "초보자를 위한 완벽 가이드", "실패하지 않기 위한 체크리스트", "요즘 고객들이 가장 궁금해하는 이야기", "실제 이용 전 준비하면 좋은 것들", "우리 업체가 중요하게 생각하는 3가지", "한눈에 보는 서비스 이용 과정"];
  const queues = new Map();

  function shuffle(items) {
    const copy = [...new Set(items)];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }
  function nextItems(key, source, count = 3) {
    let queue = queues.get(key) || [];
    const usable = new Set(source);
    queue = queue.filter(item => usable.has(item));
    if (queue.length < count) queue.push(...shuffle(source.filter(item => !queue.includes(item))));
    if (queue.length < count) queue.push(...shuffle(source));
    const selected = queue.splice(0, count);
    queues.set(key, queue);
    return selected;
  }
  function catalogFor(value) {
    const normalized = (value || "").toLowerCase().replace(/\s/g, "");
    return industries.find(group => group.keys.some(key => normalized.includes(key.toLowerCase().replace(/\s/g, "")))) || general;
  }
  function addSuggestions(input, type, businessInput, moodInput = null) {
    if (!input || input.dataset.smartSuggestions === "ready") return;
    input.dataset.smartSuggestions = "ready";
    const wrap = document.createElement("div");
    wrap.className = "smart-suggest";
    wrap.innerHTML = `<div class="smart-suggest-head"><span class="smart-suggest-label">추천 예시를 눌러 바로 입력하세요</span><span class="smart-suggest-actions">${type === "images" ? '<button class="smart-suggest-dice" type="button">🎲 랜덤 스타일 적용</button>' : ''}<button class="smart-suggest-refresh" type="button">↻ 다른 추천 보기</button></span></div><div class="smart-suggest-chips"></div>`;
    input.insertAdjacentElement("afterend", wrap);
    const chips = wrap.querySelector(".smart-suggest-chips");
    let currentSource = [];
    const sourceForCurrentInputs = () => {
      const catalog = catalogFor(businessInput?.value);
      const source = type === "moods" ? catalog.moods : catalog.images;
      if (type !== "images" || !moodInput?.value.trim()) return source;
      const mood = moodInput.value.trim();
      return source.map(style => `${style}, ${mood} 느낌을 살려 표현`);
    };
    const rotateImagePlaceholder = () => {
      if (type !== "images" || input.value || document.activeElement === input) return;
      currentSource = sourceForCurrentInputs();
      input.placeholder = `예: ${nextItems("image-placeholder", currentSource, 1)[0]}`;
    };
    const render = () => {
      const catalog = catalogFor(businessInput?.value);
      currentSource = sourceForCurrentInputs();
      const key = `${type}:${industries.indexOf(catalog)}`;
      chips.replaceChildren(...nextItems(key, currentSource).map(text => {
        const button = document.createElement("button");
        button.type = "button"; button.className = "smart-suggest-chip"; button.textContent = text;
        button.addEventListener("click", () => { input.value = text; input.dispatchEvent(new Event("input", { bubbles: true })); });
        return button;
      }));
    };
    wrap.querySelector(".smart-suggest-refresh").addEventListener("click", render);
    const rerenderLater = (() => { let timer; return () => { clearTimeout(timer); timer = setTimeout(() => { render(); rotateImagePlaceholder(); }, 250); }; })();
    businessInput?.addEventListener("input", rerenderLater);
    moodInput?.addEventListener("input", rerenderLater);
    wrap.querySelector(".smart-suggest-dice")?.addEventListener("click", () => {
      currentSource = sourceForCurrentInputs();
      input.value = nextItems("image-dice", currentSource, 1)[0];
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.focus();
    });
    if (type === "images") setInterval(rotateImagePlaceholder, 3800);
    render();
    rotateImagePlaceholder();
  }
  function rotatingPlaceholder(input, key, examples) {
    if (!input || input.value) return;
    const rotate = () => { if (!input.value && document.activeElement !== input) input.placeholder = `예: ${nextItems(key, examples, 1)[0]}`; };
    rotate(); const timer = setInterval(rotate, 3800);
    input.addEventListener("input", () => { if (input.value) clearInterval(timer); }, { once: true });
  }
  function addTopicSuggestions(input, businessInput) {
    if (!input) return;
    const wrap=document.createElement("div");wrap.className="smart-suggest";wrap.innerHTML='<div class="smart-suggest-head"><span class="smart-suggest-label">블로그 제목 예시</span><button class="smart-suggest-refresh" type="button">↻ 다른 제목</button></div><div class="smart-suggest-chips"></div>';input.insertAdjacentElement("afterend",wrap);
    const render=()=>{const business=businessInput?.value.trim()||"우리 업종";const source=topicTemplates.map(t=>`${business}, ${t}`);const chips=wrap.querySelector(".smart-suggest-chips");chips.replaceChildren(...nextItems("topics",source).map(text=>{const b=document.createElement("button");b.type="button";b.className="smart-suggest-chip";b.textContent=text;b.onclick=()=>{input.value=text;input.dispatchEvent(new Event("input",{bubbles:true}))};return b}))};wrap.querySelector("button").onclick=render;businessInput?.addEventListener("input",render);render();setInterval(()=>{if(!input.value&&document.activeElement!==input){const business=businessInput?.value.trim()||"우리 업종";input.placeholder=`예: ${business}, ${nextItems("topic-placeholder",topicTemplates,1)[0]}`}},4200)
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form[method='POST']");
    if (!form) return;
    const business = form.querySelector("[name='business']");
    const company = form.querySelector("[name='company']");
    const mood = form.querySelector("[name='style'], [name='tone']");
    const topic = form.querySelector("[name='topic']");
    const image = form.querySelector("[name='custom_image_style']");
    rotatingPlaceholder(business, "business", businessExamples);
    rotatingPlaceholder(company, "company", companyExamples);
    addSuggestions(mood, "moods", business);
    addTopicSuggestions(topic, business);
    addSuggestions(image, "images", business, mood);
  });
})();
