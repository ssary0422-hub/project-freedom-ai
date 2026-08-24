(function(){
  const I=window.PF_SPEAKING_COPY||{}; if(!Object.keys(I).length)return;
  const set=(s,v)=>{const n=document.querySelector(s);if(n&&v)n.textContent=v};
  set('.coach-kicker','SUNGEUM SPEAKING TEACHER'); set('.coach-hero h1',I.hero_title); set('.coach-hero .lead',I.hero_desc);
  set('label[for="coachInput"]',I.input_label); const input=document.getElementById('coachInput'); if(input)input.placeholder=I.input_placeholder;
  set('.coach-card .coach-hint',I.input_hint);set('#coachSubmit',I.submit);set('#coachResult .small:nth-of-type(1)',I.understood);set('#coachResult .small:nth-of-type(2)',I.sentence);set('#coachResult .small:nth-of-type(3)',I.variant);
  set('[data-variant="soft"]',I.soft);set('[data-variant="firm"]',I.firm);set('[data-quick]',I.quick);set('#speakingFeedbackSubmit',I.feedback_send);set('#coachAgain',I.again);set('#coachCharacterBubble',I.bubble);
  const pairs=Array.isArray(window.PF_TRANSLATION_PAIRS)?window.PF_TRANSLATION_PAIRS:[];
  const map=new Map(pairs.map(p=>[String(p.source||'').trim(),String(p.target||'')]));
  const replace=(root)=>{const w=document.createTreeWalker(root||document.body,NodeFilter.SHOW_TEXT),a=[];while(w.nextNode())a.push(w.currentNode);a.forEach(n=>{const raw=n.nodeValue||'',key=raw.trim(),value=map.get(key);if(value&&value!==key)n.nodeValue=raw.replace(key,value);});}; replace(document.body);
  new MutationObserver(()=>replace(document.body)).observe(document.body,{childList:true,subtree:true});
})();
