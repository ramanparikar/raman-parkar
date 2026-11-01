(() => {
"use strict";
const works = {
 BG:{sections:Array.from({length:18},(_,i)=>({value:i+1,label:"Chapter "+(i+1)})),prefix:"BG",kind:"chapter"},
 SB:{sections:Array.from({length:12},(_,i)=>({value:i+1,label:"Canto "+(i+1)+" · chapter to be selected from verified edition"})),prefix:"SB",kind:"canto"},
 CC:{sections:[{value:"ADI",label:"Ādi-līlā"},{value:"MADHYA",label:"Madhya-līlā"},{value:"ANTYA",label:"Antya-līlā"}],prefix:"CC",kind:"lila"}
};
let selected="BG";
const section=document.querySelector("#tp-section"),chapter=document.querySelector("#tp-chapter"),chapterField=document.querySelector("#tp-chapter-field"),unit=document.querySelector("#tp-unit"),ref=document.querySelector("#tp-ref"),desc=document.querySelector("#tp-description");
const pad=(n)=>String(n).padStart(2,"0");
function renderSections(){section.replaceChildren();for(const item of works[selected].sections){const option=document.createElement("option");option.value=item.value;option.textContent=item.label;section.append(option)}chapterField.hidden=selected==="BG";chapter.replaceChildren();for(let i=1;i<=99;i++){const option=document.createElement("option");option.value=i;option.textContent="Chapter "+i;chapter.append(option)}unit.value=1;unit.max=999;updateRef()}
function makeRef(){const n=Number(unit.value);if(!Number.isInteger(n)||n<1||n>999)return null;const s=section.value;if(selected==="BG")return "BG."+pad(Number(s))+"."+String(n).padStart(3,"0");if(selected==="SB")return "SB."+pad(Number(s))+"."+pad(Number(chapter.value))+"."+String(n).padStart(3,"0");return "CC."+s+"."+pad(Number(chapter.value))+"."+String(n).padStart(3,"0")}
function updateRef(){const value=makeRef();ref.textContent=value||"—";desc.textContent=selected==="SB"?"Canto selected. Chapter numbering must be entered from a verified edition before this reference can be resolved.":selected==="CC"?"Līlā selected. Chapter and unit locators remain provisional pending edition verification.":"This is a provisional Bhagavad-gītā locator, not confirmation that the verse exists in the selected printed edition."}
document.querySelectorAll("[data-work]").forEach(button=>button.addEventListener("click",()=>{selected=button.dataset.work;document.querySelectorAll("[data-work]").forEach(x=>x.classList.toggle("is-selected",x===button));renderSections()}));
section.addEventListener("change",updateRef);chapter.addEventListener("change",updateRef);unit.addEventListener("input",updateRef);
document.querySelector("#tp-open").addEventListener("click",()=>{if(selected==="SB"){desc.textContent="This canto and chapter locator is provisional. Confirm that the chapter and verse exist in the selected edition.";return}desc.textContent="Preview locator only. No verse text is stored or displayed in this development build."});
document.querySelector("#tp-copy").addEventListener("click",async()=>{const value=ref.textContent;if(!value||value==="—")return;try{await navigator.clipboard.writeText(value);document.querySelector("#tp-copy").textContent="Copied"}catch{document.querySelector("#tp-copy").textContent="Select and copy: "+value}});
const pattern=/^BG\.\d{2}\.\d{3}$|^SB\.\d{2}\.\d{2}\.\d{3}$|^CC\.(ADI|MADHYA|ANTYA)\.\d{2,3}\.\d{3}$/;
document.querySelector("#tp-search-form").addEventListener("submit",event=>{event.preventDefault();const value=document.querySelector("#tp-query").value.trim().toUpperCase();const output=document.querySelector("#tp-search-result");if(pattern.test(value)){output.textContent=value+" has a recognised canonical reference format. Edition-level existence, text, rights and verification status have not yet been confirmed."}else{output.textContent="Reference format not recognised. Examples: BG.02.047 · SB.01.02.006 · CC.ADI.02.006."}});
renderSections();
})();