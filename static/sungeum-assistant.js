(() => {
  const trigger=document.getElementById('sungeumAssistantTrigger'),panel=document.getElementById('sungeumAssistantPanel'),close=document.getElementById('sungeumAssistantClose'),backdrop=document.getElementById('sungeumAssistantBackdrop'),chat=document.getElementById('sungeumChatLine'),request=document.getElementById('sungeumRequest'),send=document.getElementById('sungeumRequestSend'),next=document.getElementById('sungeumNextStep'),summary=document.getElementById('sungeumPlanSummary'),create=document.getElementById('sungeumCreateAd'),createSns=document.getElementById('sungeumCreateSns'),createPoster=document.getElementById('sungeumCreatePoster');
  if(!trigger||!panel)return;
  const callout=trigger.querySelector('.sungeum-click-callout');
  const helloCopy=['\uc548\ub155, \ub09c \uc21c\uae08\uc774\uc57c','\ub098\ub97c \ud074\ub9ad\ud574\ubd10','\ub0b4\uac00 \ub3c4\uc640\uc904\uac8c'];
  let helloIndex=0;
  const rotateHello=()=>{if(callout&&!panel.classList.contains('is-open')){callout.textContent=helloCopy[helloIndex%helloCopy.length];helloIndex+=1;}};
  rotateHello();
  setInterval(rotateHello,4200);
  const liveStatus=trigger.querySelector('.sungeum-live-status');
  const defaultCallout=callout?.textContent||'순금이에게 물어보기',defaultStatus=liveStatus?.dataset.default||'';
  const mascots=()=>document.querySelectorAll('.sungeum-assistant-trigger .sungeum-alive,.sungeum-assistant-head .sungeum-alive');
  let moodTimer;
  const moodCopy={working:['순금이가 처리 중이에요','꼼꼼히 작업 중'],approved:['완성했어요! 🐾','순금 검수 완료'],failed:['잠깐만요, 다시 볼게요','재시도 준비'],listening:['말씀해 주세요 👂','듣고 있어요']};
  const setMood=(mood,duration=0)=>{clearTimeout(moodTimer);mascots().forEach(m=>{m.classList.remove('is-listening','is-working','is-approved','is-failed');if(mood)m.classList.add(`is-${mood}`)});if(callout)callout.textContent=moodCopy[mood]?.[0]||(localStorage.getItem('sungeum_assistant_opened')==='1'?'순금이':defaultCallout);if(liveStatus)liveStatus.textContent=moodCopy[mood]?.[1]||defaultStatus;if(duration)moodTimer=setTimeout(()=>setMood(panel.classList.contains('is-open')?'listening':''),duration)};
  window.SungeumMotion={setState:setMood};
  document.addEventListener('sungeum:state',event=>{const detail=event.detail||{};setMood(detail.state||'',Number(detail.duration)||0)});
  const open=value=>{panel.classList.toggle('is-open',value);backdrop?.classList.toggle('is-open',value);panel.setAttribute('aria-hidden',String(!value));trigger.setAttribute('aria-expanded',String(value));if(value&&callout){callout.textContent='순금이';localStorage.setItem('sungeum_assistant_opened','1')}setMood(value?'listening':'')};
  if(callout&&localStorage.getItem('sungeum_assistant_opened')==='1')callout.textContent='순금이';
  trigger.onclick=()=>open(true);close.onclick=()=>open(false);backdrop.onclick=()=>open(false);document.addEventListener('keydown',e=>e.key==='Escape'&&open(false));
  const replies={campaign:'좋아요. 이번 주 목표와 대표 상품 하나부터 알려주세요. 광고·SNS·포스터를 묶어서 준비할게요.',quiet:'손님이 적은 시간대를 채울 타임세일 광고가 좋아요. 할인할 상품 하나만 정해 주세요.',stock:'남은 수량과 가능한 할인 폭을 알려주세요. 재고 소진용 홍보를 바로 만들게요.',weather:'날씨에 맞춘 방문 혜택이나 배달 홍보가 좋아요. 대표 상품부터 골라주세요.'};
  const starters={campaign:'이번 주 대표 상품을 홍보하고 싶어',quiet:'손님이 적어서 오늘 타임세일 홍보가 필요해',stock:'남은 재고를 오늘 소진하고 싶어',weather:'날씨가 좋지 않아 배달이나 방문 혜택을 홍보하고 싶어'};
  panel.querySelectorAll('[data-sungeum-action]').forEach(button=>button.onclick=()=>{panel.querySelectorAll('[data-sungeum-action]').forEach(x=>x.classList.remove('is-selected'));button.classList.add('is-selected');const key=button.dataset.sungeumAction;setMood('listening',900);chat.innerHTML=`<span>🐾</span><p><strong>순금이</strong><br>${replies[key]}</p>`;request.value=starters[key];request.focus()});
  const prepare=()=>{const value=request.value.trim();if(value.length<3){setMood('listening');chat.innerHTML='<span>🐾</span><p><strong>순금이</strong><br>홍보할 상품이나 상황을 조금만 더 알려주세요.</p>';return}setMood('working');const stock=/재고|남았|소진/.test(value),weather=/비|눈|날씨|배달/.test(value),quiet=/손님|한가|타임세일/.test(value);const style=stock?'오늘 한정 재고 소진, 긴급성과 혜택이 분명한 분위기':weather?'날씨 맞춤 방문 또는 배달 혜택, 따뜻하고 친근한 분위기':quiet?'한가한 시간대 타임세일, 즉시 행동을 유도하는 분위기':'대표 상품의 장점과 혜택이 분명한 친근한 분위기';const brief=encodeURIComponent(value),mood=encodeURIComponent(style);summary.textContent=`순금이가 요청을 정리했어요: ${value}`;create.href=`/ads-generator?assistant_brief=${brief}&style=${mood}`;createSns.href=`/sns?assistant_brief=${brief}&style=${mood}`;createPoster.href=`/poster?assistant_brief=${brief}`;next.hidden=false;chat.innerHTML='<span>🐾</span><p><strong>순금이</strong><br>상황에 맞춰 준비했어요. 광고·SNS·포스터 중 필요한 걸 골라주세요.</p>';localStorage.setItem('sungeum_last_brief',value);setTimeout(()=>setMood('approved',900),650)};
  send.onclick=prepare;request.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();prepare()}});
  const query=new URLSearchParams(location.search);if(query.get('sungeum')==='open')open(true);if(query.get('brief')){request.value=query.get('brief');prepare()}
  const scheduleHello=()=>setTimeout(()=>{if(!panel.classList.contains('is-open')&&!document.body.classList.contains('is-generating'))setMood('listening',950);scheduleHello()},9000+Math.random()*6000);scheduleHello();
})();
