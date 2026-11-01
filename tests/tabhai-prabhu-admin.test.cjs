"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class Element {
  constructor(id="") { this.id=id; this.listeners={}; this.children=[]; this.textContent=""; this.download=""; this.href=""; this.type=""; this.colSpan=1; }
  addEventListener(name,fn){(this.listeners[name] ||= []).push(fn)}
  dispatch(name,event={}){for(const fn of this.listeners[name]||[])fn(event)}
  replaceChildren(){this.children=[]}
  append(child){this.children.push(child)}
  remove(){}
  click(){this.clicked=true}
  reset(){this.resetCalled=true}
  reportValidity(){return true}
}
class FakeForm extends Element {
  constructor(values){super();this.values=values;const controls={};for(const [k,v] of Object.entries(values))controls[k]={type:v==="yes"||v==="no"?"checkbox":"text",checked:v==="yes"};this.elements={namedItem:name=>controls[name]||null}}
  reset(){this.resetCalled=true}
}
function boot(){
 const ids=["#ta-status","#ta-edition-form","#ta-volume-form","#ta-edition-rows","#ta-volume-rows","#ta-export-editions","#ta-export-volumes","#ta-clear"];
 const els=Object.fromEntries(ids.map(id=>[id,new Element(id)]));
 const document={querySelector:s=>els[s],createElement:()=>new Element("a"),body:{append(){} }};
 const downloads=[];
 class FormDataMock{constructor(form){this.form=form}get(k){const v=this.form.values[k];return v==="yes"||v==="no"?null:v}}
 const URLMock={createObjectURL:blob=>{downloads.push(blob);return "blob:test"},revokeObjectURL(){}};
 vm.runInNewContext(fs.readFileSync("tabhai-prabhu-admin.js","utf8"),{document,FormData:FormDataMock,Blob,URL:URLMock,Date,Number,console});
 return {els,downloads};
}
const candidate={
 work_code:"SB",edition_code:"SB_TEST_1972",title:"Srimad-Bhagavatam First Canto",publisher:"Publisher",
 publication_year:"1972",edition_language:"English",isbn:"",pages:"",metadata_source_url:"https://example.org/catalogue",
 candidate_state:"candidate_not_selected",edition_family:"First Canto historical edition",rights_chain_status:"authority_unverified",
 textual_revision_status:"unknown",notes:"Catalogue discovery only"
};
const volume={
 work_code:"SB",edition_code:"SB_TEST_1972",volume_number:"1",volume_title:"First Canto",publisher:"Publisher",
 place_of_publication:"Mumbai",edition_statement:"First edition",impression_number:"First impression",
 publication_year:"1972",copyright_year:"1972",isbn_or_catalogue_number:"",total_pages:"400",
 first_section:"Canto 1 Chapter 1",last_section:"Canto 1 Chapter 19",first_printed_page:"i",
 last_printed_page:"388",title_page_checked:"yes",copyright_page_checked:"yes",
 table_of_contents_checked:"yes",numbering_checked:"yes",independent_checker:"Reviewer",
 checked_on:new Date().toISOString().slice(0,10),physical_copy_reference:"Library shelf A1",
 evidence_notes:"Physical copy inspected"
};
test("edition candidate is recorded only as unselected discovery metadata",()=>{
 const {els}=boot();let prevented=false;
 els["#ta-edition-form"].dispatch("submit",{preventDefault(){prevented=true},currentTarget:new FakeForm(candidate)});
 assert.equal(prevented,true);
 assert.match(els["#ta-status"].textContent,/not physically verified/);
 assert.equal(els["#ta-edition-rows"].children.length,1);
});
test("HTTP catalogue sources are rejected",()=>{
 const {els}=boot();els["#ta-edition-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm({...candidate,metadata_source_url:"http://example.org"})});
 assert.match(els["#ta-status"].textContent,/HTTPS/);
 assert.equal(els["#ta-edition-rows"].children.length,0);
});
test("volume record cannot be added without a matching candidate",()=>{
 const {els}=boot();els["#ta-volume-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(volume)});
 assert.match(els["#ta-status"].textContent,/Add the matching edition candidate first/);
});
test("volume record requires matching candidate and all inspection checks",()=>{
 const {els}=boot();
 els["#ta-edition-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(candidate)});
 els["#ta-volume-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm({...volume,numbering_checked:"no"})});
 assert.match(els["#ta-status"].textContent,/All four physical inspection checks/);
 assert.equal(els["#ta-volume-rows"].children.length,0);
});
test("duplicate volume number is rejected",()=>{
 const {els}=boot();
 els["#ta-edition-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(candidate)});
 els["#ta-volume-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(volume)});
 els["#ta-volume-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(volume)});
 assert.match(els["#ta-status"].textContent,/already recorded/);
 assert.equal(els["#ta-volume-rows"].children.length,1);
});
test("volume CSV export creates a local download and reports no upload",()=>{
 const {els,downloads}=boot();
 els["#ta-edition-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(candidate)});
 els["#ta-volume-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(volume)});
 els["#ta-export-volumes"].dispatch("click");
 assert.equal(downloads.length,1);
 assert.match(els["#ta-status"].textContent,/No upload or database write/);
});

test("edition candidate export uses the validator-compatible column contract",async()=>{
 const {els,downloads}=boot();
 els["#ta-edition-form"].dispatch("submit",{preventDefault(){},currentTarget:new FakeForm(candidate)});
 els["#ta-export-editions"].dispatch("click");
 assert.equal(downloads.length,1);
 const csv=await downloads[0].text();
 for(const column of ["work_code","edition_code","title","edition_language","metadata_source_url","candidate_state","edition_family","rights_chain_status","textual_revision_status","notes"]) assert.ok(csv.includes(column));
 assert.ok(csv.includes("candidate_not_selected"));
});
