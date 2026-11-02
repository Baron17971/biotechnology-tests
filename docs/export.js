"use strict";
/* ייצוא המבחן לוורד (docx): טור א׳ לפי סדר הסל, טור ב׳ מערבב שאלות ואפשרויות.
   עטוף בפונקציה כדי לא להתנגש בשמות של app.js. */
(() => {

const D = window.docx;
const HEB_LETTERS = "אבגדהוזחטי";
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
const FIG_MAX_W = 430; // פיקסלים של docx (1/96 אינץ')
const FIG_MAX_H = 360;
const GRAY = "666666";
const FONT_SIZE = 24; // חצאי נקודה: 12pt
const LINE_15 = 360;
const NAVY="173553", PALE="F1F5F9", BORDER="D5E0E9", SOFT="52677D"; // רווח שורות 1.5 (240 = שורה אחת)

const optLabel = (style, i) => (style === "upper-roman" ? ROMAN[i] : HEB_LETTERS[i]);

/* ---------- אבני בניין ---------- */

const HEBREW = /[֐-׿]/;
const LRM = "‎";
const RLM = "‏";
const selectedFont = () => ["Arial","Tahoma","David","Varela Round"].includes(state.header.font) ? state.header.font : "Arial";

/** קטע בלי עברית (רצף DNA, מספר רומי) נעטף בסימני LRM כדי שהגרשים והנקודות לא יקפצו לצד הלא נכון */
function run(text, o = {}) {
  const hebrew = HEBREW.test(text);
  const t = !hebrew && /[A-Za-z0-9]/.test(text) ? `${LRM}${text}${LRM}` : text;
  return new D.TextRun({ size: FONT_SIZE, font: selectedFont(), text: t, rightToLeft: hebrew, bold: o.bold, italics: o.italics, color: o.color });
}

function para(children, o = {}) {
  return new D.Paragraph({
    bidirectional: true,
    children: [new D.TextRun({ size: FONT_SIZE, font: selectedFont(), text: RLM, rightToLeft: true }), ...[].concat(children).filter(Boolean)],
    alignment: o.center ? D.AlignmentType.CENTER : undefined,
    spacing: { before: o.before ?? 0, after: o.after ?? 80, line: LINE_15 },
    keepNext: o.keepNext,
    border: o.border,
    shading: o.shading,
  });
}

/** טקסט עם ירידות שורה → פסקה לכל שורה; prefix (למשל אות הסעיף) נכנס לשורה הראשונה */
function lines(text, o = {}, prefix = null) {
  return String(text ?? "").split("\n").map((line, i) =>
    para([i === 0 ? prefix : null, run(line, o)], o));
}

async function figure(q, f) {
  const buf = await (await fetch(`figures/${q.exam}/${f}`)).arrayBuffer();
  const bmp = await createImageBitmap(new Blob([buf]));
  const k = Math.min(1, FIG_MAX_W / bmp.width, FIG_MAX_H / bmp.height);
  return para(new D.ImageRun({
    type: "png", data: buf,
    transformation: { width: Math.round(bmp.width * k), height: Math.round(bmp.height * k) },
  }), { center: true, after: 120 });
}

const figures = (q, list) => Promise.all((list || []).map((f) => figure(q, f)));

function table(t) {
  const n = t.headers.length;
  const cell = (text, head) => new D.TableCell({
    children: lines(text, { bold: head, after: 0 }),
    shading: head ? { fill: "EEEEEE", type: D.ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 100, right: 100 },
  });
  return [
    new D.Table({
      visuallyRightToLeft: true,
      width: { size: 9000, type: D.WidthType.DXA },
      columnWidths: Array(n).fill(Math.floor(9000 / n)),
      rows: [
        new D.TableRow({ tableHeader: true, children: t.headers.map((h) => cell(h, true)) }),
        ...t.rows.map((r) => new D.TableRow({ children: r.map((c) => cell(c, false)) })),
      ],
    }),
    para(run(""), { after: 60 }),
  ];
}

/** אפשרויות לשאלה אמריקאית; perm = סדר ההצגה (בטור ב׳ – מעורבב) */
function optionParas(opts, style, perm) {
  // RLM אחרי התווית מפריד בין "I." לבין מילה לועזית שאחריה, כך שהתווית נשארת בצד ימין
  const sep = () => new D.TextRun({ size: FONT_SIZE, font: selectedFont(), text: `${RLM}  `, rightToLeft: true });
  return perm.flatMap((src, i) => opts[src].split("\n").map((line, j) =>
    para([j === 0 ? run(`${optLabel(style, i)}.`) : run("      "), sep(), run(line)], { after: 40 })));
}

/** רשימה נפתחת → מחסן היגדים במסגרת, כדי שהתלמיד יידע מתוך מה לבחור */
function bank(inter) {
  if (!inter) return [];
  if (inter.kind === "true_false") return [para(run("לכל היגד כתבו: נכון / לא נכון", { bold: true }))];
  if (!inter.options) return [];
  const bullet = (o) => para([run("•"), new D.TextRun({ size: FONT_SIZE, font: selectedFont(), text: `${RLM}  `, rightToLeft: true }), run(o)], { after: 0 });
  const cell = new D.TableCell({
    children: [para(run("מחסן היגדים – בחרו מתוך:", { bold: true }), { after: 40 }), ...inter.options.map(bullet)],
    margins: { top: 80, bottom: 80, left: 160, right: 160 },
  });
  return [
    new D.Table({
      visuallyRightToLeft: true,
      width: { size: 9000, type: D.WidthType.DXA },
      columnWidths: [9000],
      rows: [new D.TableRow({ children: [cell] })],
    }),
    para(run(""), { after: 60 }),
  ];
}

const box = { style: D.BorderStyle.SINGLE, color: "999999", space: 4 };

/* ---------- רכיבי עיצוב מסמך ---------- */
function cell(content,opts={}) {
  return new D.TableCell({
    children: Array.isArray(content) ? content : [content],
    shading:opts.fill ? {fill:opts.fill,color:"auto",type:D.ShadingType.CLEAR} : undefined,
    borders:{top:{style:D.BorderStyle.SINGLE,size:1,color:opts.border||BORDER},
      bottom:{style:D.BorderStyle.SINGLE,size:1,color:opts.border||BORDER},
      left:{style:D.BorderStyle.SINGLE,size:1,color:opts.border||BORDER},
      right:{style:D.BorderStyle.SINGLE,size:1,color:opts.border||BORDER}},
    margins:{top:opts.pad??140,bottom:opts.pad??140,left:170,right:170},
    verticalAlign:D.VerticalAlign.CENTER
  });
}
function designedTable(rows,widths) {
  return new D.Table({visuallyRightToLeft:true,
    width:{size:9000,type:D.WidthType.DXA},columnWidths:widths,
    rows:rows.map((row)=>new D.TableRow({cantSplit:true,
      children:row}))});
}
function styledText(text,size=24,color=NAVY,bold=false) {
  return new D.TextRun({text:String(text),font:selectedFont(),size,color,bold,rightToLeft:true});
}
function dataCell(label,value) {
  return cell([para(styledText(label,18,SOFT),{after:45}),
    para(styledText(value || "________________",23,NAVY,true),{after:0})],{fill:PALE,pad:130});
}
function sectionBanner(title,points) {
  return designedTable([[cell(para(styledText(title+"  ("+points+" נקודות)",26,"FFFFFF",true),
    {center:true,after:0}),{fill:NAVY,border:NAVY,pad:170})]],[9000]);
}
function questionTitle(n,pts) {
  // פסקת Word רגילה, ללא טבלה וללא רקע או מסגרת.
  return para([
    styledText("שאלה "+n,24,"111111",true),
    styledText(" ("+(pts ?? "—")+" נקודות)",24,"111111",true)
  ],{before:135,after:80,keepNext:true});
}

function answerRule() {
  return new D.Paragraph({bidirectional:true,children:[styledText(" ",22)],
    spacing:{before:0,after:80,line:350},
    border:{bottom:{style:D.BorderStyle.SINGLE,color:"AFC1D1",size:4,space:2}}});
}

/* ---------- שאלה ---------- */

async function questionBlocks(entry, n, perms) {
  const q = QS.get(entry.id);
  const style = BANK.exams[q.exam].option_style || "hebrew";
  const pts = effectivePoints(entry);
  const out = [questionTitle(n,pts)];

  if (q.passage) {
    const ps = q.passage;
    out.push(para(run(ps.title, { bold: true }), { center: true, after: 100 }));
    if (ps.intro) out.push(...lines(ps.intro, { italics: true }));
    out.push(...lines(ps.text, { after: 100 }));
    if (ps.credit) out.push(...lines(ps.credit, { color: GRAY }));
  }
  if (q.stem) out.push(...lines(q.stem));
  out.push(...await figures(q, q.stem_figures));

  if (q.type === "mc") {
    out.push(...await figures(q, q.figures));
    out.push(...optionParas(q.options, style, perms[`${q.id}|`] || q.options.map((_, i) => i)));
  } else if (q.items) {
    for (const p of q.items.filter((it) => entry.items.includes(it.label))) {
      out.push(para(run(""), { after: 0 }));
      for (const [i, part] of itemOrder(p).entries()) {
        const label = i === 0 ? run(`${p.label}.  `, { bold: true }) : null;
        if (part === "intro") out.push(...lines(p.intro, {}, label));
        if (part === "figures") out.push(...await figures(q, p.figures));
        if (part === "table") out.push(...table(p.table));
        if (part === "text") out.push(...lines(p.text, {}, label));
      }
      if (p.options) {
        out.push(...optionParas(p.options, style, perms[`${q.id}|${p.label}`] || p.options.map((_, i) => i)));
      }
      out.push(...bank(p.interactive));
    }
  }
  if (q.type === "open") {
    const count = entry.lines == null ? Math.max(0,Math.min(20,Number(state.header.answerLines ?? 4))) : entry.lines;
    if (count > 0) {
      out.push(para(run("תשובה:",{bold:true}),{before:160,after:80}));
      for(let i=0;i<count;i++) out.push(answerRule());
    }
  }
  if (isOnline(q)) {
    out.push(para(run("שאלה זו דורשת עבודה בכלים מקוונים (Entrez / BLAST) – יש לפתור אותה מול מחשב.",
      { italics: true }), { border: { top: box, bottom: box, left: box, right: box }, before: 120 }));
  }
  return out;
}

/* ---------- מסמך ---------- */

function inferredExamTopic() {
 const subs=new Map(), units=new Map();
 for(const entry of state.cart) {
  const q=QS.get(entry.id); if(!q)continue;
  const sub=SUBS.get(q.main),unit=UNITS.get(q.unit);
  if(sub)subs.set(sub.name,(subs.get(sub.name)||0)+1);
  if(unit)units.set(unit.name,(units.get(unit.name)||0)+1);
 }
 if(subs.size===1)return [...subs.keys()][0].split(" – ")[0];
 if(units.size===1)return [...units.keys()][0];
 if(units.size>1)return [...units.keys()].slice(0,3).join(" • ");
 return "ביוטכנולוגיה";
}
async function headerBlocks(version) {
 const h=state.header,out=[];
 if(state.logo){
  try {
   const res=await fetch(state.logo),buf=await res.arrayBuffer(),jpg=state.logo.startsWith("data:image/jpeg");
   const bmp=await createImageBitmap(new Blob([buf],{type:jpg?"image/jpeg":"image/png"}));
   const k=Math.min(1,116/bmp.width,110/bmp.height);
   out.push(new D.Paragraph({bidirectional:true,spacing:{after:0},children:[
    new D.ImageRun({type:jpg?"jpg":"png",data:buf,
     transformation:{width:Math.max(1,Math.round(bmp.width*k)),height:Math.max(1,Math.round(bmp.height*k))},
     floating:{horizontalPosition:{relative:D.HorizontalPositionRelativeFrom.PAGE,offset:1050000},
      verticalPosition:{relative:D.VerticalPositionRelativeFrom.PAGE,offset:950000},
      behindDocument:true,allowOverlap:true,wrap:{type:D.TextWrappingType.NONE}}})
   ]}));
  }catch(e){console.warn("Cannot place logo",e);}
 }
 out.push(para(styledText(h.school||"שם בית הספר",36,NAVY,true),{after:90}));
 out.push(para(styledText(" ",16),{after:120}));
 out.push(para(styledText(h.exam||"מבחן מסכם",38,NAVY,true),{center:true,after:65,keepNext:true}));
 out.push(para(styledText("נושא: "+inferredExamTopic(),24,SOFT),{center:true,after:140}));
 if(version==="B")out.push(para(styledText("טור ב׳",25,NAVY,true),{center:true,after:90}));
 const duration=h.duration?h.duration+" "+(h.durationUnit||"דקות"):"";
 out.push(designedTable([
  [dataCell("שכבת גיל / כיתה",h.cls),dataCell("תאריך",h.date)],
  [dataCell("שם התלמיד/ה",h.student||"____________________"),dataCell("משך הבחינה",duration)]
 ],[4500,4500]));
 out.push(para(styledText("סך הכול: 100 נקודות",22,NAVY,true),{before:130,after:90}));
 if(h.instructions){out.push(para(styledText("הנחיות:",21,NAVY,true),{after:40}));out.push(...lines(h.instructions,{after:70}));}
 out.push(para(run(" "),{after:80}));return out;
}

function sectionedEntries(entries) {
  if (state.header.layout !== "sections") return [{label:"",entries}];
  const types=[["mc","חלק א׳ — שאלות רבות ברירה"],["tf","חלק ב׳ — נכון / לא נכון"],["open","חלק ג׳ — שאלות פתוחות"]];
  const available=types.map(([type,label])=>({label,entries:entries.filter(e=>QS.get(e.id).type===type)})).filter(x=>x.entries.length);
  return available.map((x,i)=>({...x,label:"חלק "+("אבגדה"[i])+"׳ — "+x.label.split(" — ")[1]}));
}
function orderEntries(entries) {
  return sectionedEntries(entries).flatMap(s=>s.entries);
}

async function buildDoc(version, entries, perms) {
  const children = await headerBlocks(version);
  let number=1;
  for (const section of sectionedEntries(entries)) {
    if(section.label) {
      const points=section.entries.reduce((n,e)=>n+(effectivePoints(e)||0),0);
      children.push(sectionBanner(section.label,points));
    }
    for(const [i,entry] of section.entries.entries()) {
      if(i>0) children.push(para(run(" "),{before:90,after:0}));
      children.push(...await questionBlocks(entry,number++,perms));
    }
  }
  return new D.Document({
    styles: { default: { document: { run: { font: selectedFont() } } } },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 },
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      footers: { default: new D.Footer({ children: [new D.Paragraph({
        alignment: D.AlignmentType.CENTER, children: [new D.TextRun({ size: FONT_SIZE, font: selectedFont(), children: [D.PageNumber.CURRENT] })] })] }) },
      children,
    }],
  });
}

/* ---------- טור ב׳ ---------- */

function shuffled(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** ערבוב ששונה מהסדר המקורי (כשיש יותר מפריט אחד) */
function shuffleDifferent(arr) {
  if (arr.length < 2) return [...arr];
  let a;
  do { a = shuffled(arr); } while (a.every((x, i) => x === arr[i]));
  return a;
}

/** סדר מעורבב לכל קבוצת אפשרויות במבחן: מפתח "שאלה|סעיף" → אינדקסים מקוריים לפי סדר ההצגה */
function optionPerms(entries) {
  const perms = {};
  for (const entry of entries) {
    const q = QS.get(entry.id);
    if (q.type === "mc") perms[`${q.id}|`] = shuffleDifferent(q.options.map((_, i) => i));
    for (const p of (q.items || []).filter((it) => it.options && entry.items.includes(it.label))) {
      perms[`${q.id}|${p.label}`] = shuffleDifferent(p.options.map((_, i) => i));
    }
  }
  return perms;
}

/** טבלת המרה למורה (מוצגת בסל, לא נכנסת לקובץ): מיקום כל שאלה וכל אפשרות בטור ב׳ */
function renderConversion(entriesB, perms) {
  const rows = orderEntries(state.cart).map((entry, i) => {
    const q = QS.get(entry.id);
    const style = BANK.exams[q.exam].option_style || "hebrew";
    const opts = Object.entries(perms).filter(([k]) => k.startsWith(`${q.id}|`)).map(([k, perm]) => {
      const part = k.split("|")[1];
      const map = perm.map((src, to) => [src, to]).sort((a, b) => a[0] - b[0])
        .map(([src, to]) => `${optLabel(style, src)}→${optLabel(style, to)}`).join(", ");
      return `${part ? `סעיף ${part}: ` : ""}${map}`;
    });
    return `<tr><td>${i + 1}</td><td>${entriesB.indexOf(entry) + 1}</td><td>${opts.map(esc).join("<br>") || "—"}</td></tr>`;
  }).join("");
  document.getElementById("convert").innerHTML = `<b>טבלת המרה לטור ב׳</b> (למורה – לא נכנסת לקובץ)
    <table><tr><th>טור א׳</th><th>טור ב׳</th><th>אפשרויות (א׳→ב׳)</th></tr>${rows}</table>`;
}

/* ---------- הורדה ---------- */

function fileName(version) {
  const base = (state.header.exam || "מבחן").replace(/[\\/:*?"<>|]/g, " ").trim();
  return `${base}${version === "B" ? " - טור ב" : ""}.docx`;
}

/** בונה את הקובץ ומחזיר Blob (גם לבדיקות) */
async function examBlob(version) {
  const points = state.cart.map(effectivePoints);
  if(!state.cart.length || points.some(p=>!Number.isFinite(p)||p<0) || Math.abs(points.reduce((a,b)=>a+b,0)-100)>0.001) {
    throw Error("יש להשלים ניקוד מדויק של 100 נקודות לפני הייצוא.");
  }
  let entries = orderEntries(state.cart);
  let perms = {};
  if (version === "B") {
    if(state.header.layout==="sections") {
      entries=sectionedEntries(state.cart).flatMap(sec=>shuffleDifferent(sec.entries));
    } else {
      entries=shuffleDifferent(state.cart);
    }
    perms = optionPerms(entries);
    renderConversion(entries, perms);
  }
  return D.Packer.toBlob(await buildDoc(version, entries, perms));
}

async function download(version) {
  const status = document.getElementById("export-status");
  status.textContent = "מכין את הקובץ…";
  try {
    const blob = await examBlob(version);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fileName(version);
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    status.textContent = `הקובץ "${a.download}" ירד.`;
  } catch (e) {
    console.error(e);
    status.textContent = `שגיאה בייצוא: ${e.message}`;
  }
}

document.getElementById("export-a").addEventListener("click", () => download("A"));
document.getElementById("export-b").addEventListener("click", () => download("B"));
window.examBlob = examBlob;

})();
