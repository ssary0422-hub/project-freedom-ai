(function(){
  const I=window.PF_SPEAKING_COPY||{}; if(!Object.keys(I).length)return;
  const set=(s,v)=>{const n=document.querySelector(s);if(n&&v)n.textContent=v};
  const setAll=(s,v)=>{if(!v)return;document.querySelectorAll(s).forEach(n=>{n.textContent=v});};
  function apply(){
    set('.coach-kicker','SUNGEUM SPEAKING TEACHER'); set('.coach-hero h1',I.hero_title); set('.coach-hero .lead',I.hero_desc);
    set('label[for="coachInput"]',I.input_label); const input=document.getElementById('coachInput'); if(input)input.placeholder=I.input_placeholder;
    set('.coach-card .coach-hint',I.input_hint);set('#coachSubmit',I.submit);
    const resultLabels=document.querySelectorAll('#coachResult > .small'); [I.understood,I.sentence,I.variant].forEach((v,i)=>{if(resultLabels[i]&&v)resultLabels[i].textContent=v});
    set('[data-variant="soft"]',I.soft);set('[data-variant="firm"]',I.firm);set('[data-quick]',I.quick);set('#speakingFeedbackSubmit',I.feedback_send);set('#coachAgain',I.again);set('#coachCharacterBubble',I.bubble);
    set('.coach-tone-label',I.tone); set('.coach-tone-options [data-tone="natural"]',I.natural); set('.coach-tone-options [data-tone="polite"]',I.polite); set('.coach-tone-options [data-tone="friendly"]',I.friendly); set('.coach-tone-options [data-tone="firm"]',I.firm);
    set('.coach-category-picker .coach-tone-label',I.examples); set('.coach-example-next',I.next_example); set('.coach-length-picker .coach-tone-label',I.length);
    set('.coach-length-options [data-length="normal"]',I.normal); set('.coach-length-options [data-length="short"]',I.short); set('.coach-length-options [data-length="detail"]',I.detail); set('.coach-length-options [data-length="long"]',I.long);
    set('.coach-confirm-text',I.confirm); set('[data-confirm="yes"]',I.yes); set('[data-confirm="no"]',I.no); set('.coach-copy',I.copy);
    set('#speakingFeedback .fw-bold',I.feedback_title); set('#speakingFeedbackSubmit',I.feedback_send); set('#speakingFeedbackThanks',I.thanks);
    const feedback=document.getElementById('speakingFeedback'); if(feedback){const buttons=feedback.querySelectorAll('[data-review-rating]');[I.helpful,I.neutral,I.not_helpful].forEach((v,i)=>{if(buttons[i]&&v)buttons[i].textContent=v});if(I.feedback_placeholder)feedback.querySelector('textarea')?.setAttribute('placeholder',I.feedback_placeholder)}
  }
  const pairs=Array.isArray(window.PF_TRANSLATION_PAIRS)?window.PF_TRANSLATION_PAIRS:[];
  const map=new Map(pairs.map(p=>[String(p.source||'').trim(),String(p.target||'')]));
  const replace=(root)=>{const w=document.createTreeWalker(root||document.body,NodeFilter.SHOW_TEXT),a=[];while(w.nextNode())a.push(w.currentNode);a.forEach(n=>{const raw=n.nodeValue||'',key=raw.trim(),value=map.get(key);if(value&&value!==key)n.nodeValue=raw.replace(key,value);});};
  const run=()=>{apply();replace(document.body)}; if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
  let busy=false;new MutationObserver(()=>{if(busy)return;busy=true;requestAnimationFrame(()=>{run();busy=false})}).observe(document.body,{childList:true,subtree:true});
})();
