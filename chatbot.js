(() => {
  "use strict";
  if (document.getElementById("rp-chat-host")) return;
  const endpoint = "https://akfnlsyvjlxkdibfhuzy.supabase.co/functions/v1/raman-chat";
  // These are the already-published Supabase client credentials also used by the Yatra page.
  // They identify the project only; no service-role or provider secret is included.
  const publicKey = "sb_publishable_TbNJKpXMKCv6bcjSDgpUwA_FLS1SsFz";
  const anonJwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFrZm5sc3l2amx4a2RpYmZodXp5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI2NzEzMDMsImV4cCI6MjEwODI0NzMwM30.FcL_imdBoozzL2W5_iJ47ZwqcuJerGpCzvyjItgp5qc";
  const host = document.createElement("div"); host.id = "rp-chat-host";
  const shadow = host.attachShadow({mode:"open"});
  shadow.innerHTML = `
    <style>
      :host{all:initial;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#27251f}
      *{box-sizing:border-box}.launcher{position:fixed;z-index:2147483000;right:20px;bottom:20px;border:0;border-radius:999px;background:#713b23;color:#fff;padding:14px 18px;font-size:15px;font-weight:700;box-shadow:0 5px 22px #0003;cursor:pointer}
      .panel{position:fixed;z-index:2147483001;right:18px;bottom:82px;width:min(390px,calc(100vw - 24px));height:min(600px,calc(100dvh - 108px));background:#fffdf8;border:1px solid #ddcfb8;border-radius:18px;box-shadow:0 14px 46px #0003;display:none;grid-template-rows:auto auto 1fr auto auto;overflow:hidden}
      .panel[open]{display:grid}.head{display:flex;align-items:center;justify-content:space-between;padding:15px 16px;background:#f7efdf;border-bottom:1px solid #e5dac8}.brand{font-size:16px;font-weight:750;color:#542e1d}.sub{font-size:11px;color:#665b4b;margin-top:2px}.head button{border:0;background:transparent;font-size:23px;cursor:pointer;color:#51412e}
      .privacy{padding:8px 13px;background:#fff8e9;color:#68583e;font-size:11px;line-height:1.4;border-bottom:1px solid #efe5d6}.messages{overflow:auto;padding:14px;display:flex;flex-direction:column;gap:12px;scroll-behavior:smooth}.msg{border-radius:13px;padding:11px 12px;font-size:13px;line-height:1.55;max-width:96%;overflow-wrap:anywhere;white-space:pre-wrap}.user{align-self:flex-end;background:#efe0ca}.bot{align-self:flex-start;background:#f2f2ee;width:100%}.msg h4{font-size:12px;margin:10px 0 4px;color:#633c22}.msg h4:first-child{margin-top:0}.passage{padding:8px 0;border-top:1px solid #ddd5ca}.verse{font-family:serif;font-size:16px;line-height:1.8;white-space:pre-wrap}.small{font-size:12px;color:#625b51}.sources a{color:#704122;text-decoration:underline}.notice{font-size:11px;color:#68583e;padding-top:8px}.composer{display:flex;gap:8px;padding:10px;border-top:1px solid #e5dac8}.composer textarea{flex:1;min-width:0;resize:none;height:48px;border:1px solid #cdbfa9;border-radius:10px;padding:9px;font:14px inherit}.composer button{border:0;border-radius:10px;background:#713b23;color:white;padding:0 14px;font-weight:700;cursor:pointer}.tools{display:flex;justify-content:space-between;align-items:center;padding:0 12px 9px;font-size:11px;color:#625b51}.tools select{padding:4px;border:1px solid #cdbfa9;border-radius:7px;background:#fffdf8}.typing{color:#655c4d;font-size:12px;font-style:italic}.error{color:#8b241e}
      @media(max-width:480px){.launcher{right:14px;bottom:14px;width:56px;height:56px;padding:0;font-size:0;display:grid;place-items:center}.launcher::before{content:"";display:block;width:20px;height:15px;border:2px solid #fff;border-radius:5px}.launcher::after{content:"";position:absolute;right:17px;bottom:16px;width:7px;height:7px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:skewY(-35deg);background:#713b23}.panel{right:8px;bottom:72px;width:calc(100vw - 16px);height:min(680px,calc(100dvh - 88px));border-radius:16px}.messages{padding:11px}}
    </style>
    <button class="launcher" aria-haspopup="dialog" aria-expanded="false">🪷 Ask Raman Parikar</button>
    <section class="panel" role="dialog" aria-label="Raman Parikar spiritual assistant" aria-modal="false">
      <header class="head"><div><div class="brand">Raman Parikar Sādhana Sāhāyaka</div><div class="sub">Scripture excerpts &amp; website information</div></div><button class="close" aria-label="Close chat">×</button></header>
      <div class="privacy">No chat history is saved. Please don’t share private or sensitive information. The library currently contains 14 selected passages, not complete scripture books.</div>
      <div class="messages" aria-live="polite"><div class="msg bot">Hare Krishna! Ask in Hindi or English about a selected scripture passage or verified Raman Parikar website information. / हरे कृष्ण! चयनित शास्त्र-संदर्भ या वेबसाइट की जानकारी पूछें।</div></div>
      <div class="tools"><label>Language <select aria-label="Answer language"><option value="en">English</option><option value="hi">हिन्दी</option></select></label><span class="state">Ready</span></div>
      <form class="composer"><textarea maxlength="1000" required aria-label="Your question" placeholder="Ask a question… / अपना प्रश्न लिखें"></textarea><button type="submit">Send</button></form>
    </section>`;
  document.body.appendChild(host);
  const $ = s => shadow.querySelector(s), launcher=$(".launcher"), panel=$(".panel"), messages=$(".messages"), form=$("form"), textarea=$("textarea"), state=$(".state");
  launcher.addEventListener("click",()=>{panel.toggleAttribute("open");launcher.setAttribute("aria-expanded",String(panel.hasAttribute("open")));if(panel.hasAttribute("open"))textarea.focus();});
  $(".close").addEventListener("click",()=>{panel.removeAttribute("open");launcher.setAttribute("aria-expanded","false");launcher.focus();});
  shadow.addEventListener("keydown",e=>{if(e.key==="Escape"&&panel.hasAttribute("open"))$(".close").click();});
  function node(tag,cls,text,parent){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;parent.appendChild(el);return el;}
  function linkLine(parent,title,url){if(!/^https:\/\/(vedabase\.io|ramanparikar\.github\.io)\//.test(url))return;const a=document.createElement("a");a.href=url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=title;a.className="source-link";parent.appendChild(a);}
  function render(data){const box=node("div","msg bot",undefined,messages);
    if(data.kind==="website"){node("h4","","Website information",box);node("div","",data.answer,box);node("h4","","Website sources",box);for(const s of data.sources||[]){linkLine(box,s.title,s.url);node("br","",undefined,box);} }
    if(data.kind==="scripture"){
      node("h4","",data.ai_available?"AI interpretation":"Source-grounded note",box);node("div","",data.interpretation,box);node("div","notice",data.ai_available?"This is an AI-generated explanation based only on the excerpts below; it is interpretation, not scripture.":"AI explanation is not configured yet. The verified excerpts and curated meanings below remain available.",box);
      node("h4","","Verified scripture excerpts",box);
      for(const p of data.passages||[]){const item=node("div","passage",undefined,box);node("strong","",p.reference,item);node("div","verse",p.original,item);node("div","small",p.transliteration,item);node("div","small",`हिन्दी भावार्थ: ${p.meaning_hi}`,item);node("div","small",`English meaning: ${p.meaning_en}`,item);linkLine(item,"Source text at Vedabase",p.url);}
      node("div","notice","Selected-source collection only; no complete book or unpublished group material is included.",box);
    }
    if(data.kind==="uncertain"){node("div","",data.answer,box);}
    messages.scrollTop=messages.scrollHeight;
  }
  form.addEventListener("submit",async e=>{e.preventDefault();const message=textarea.value.trim();if(!message)return;node("div","msg user",message,messages);textarea.value="";state.textContent="Thinking…";const typing=node("div","msg bot typing","Searching selected sources…",messages);messages.scrollTop=messages.scrollHeight;
    try{const response=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"application/json",apikey:publicKey,Authorization:`Bearer ${anonJwt}`},body:JSON.stringify({message,language:$("select").value})});const data=await response.json();typing.remove();if(!response.ok)throw new Error(response.status===429?"Too many questions in a short period. Please wait a few minutes.":"The assistant is temporarily unavailable. Please try again shortly.");render(data);state.textContent="Ready";}catch(err){typing.remove();node("div","msg bot error",err.message,messages);state.textContent="Ready";} });
})();

