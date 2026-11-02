"""בניית דף בדיקה לפיילוט: מחשב תת-נושא ראשי לכל שאלה, בודק עקביות,
ומייצר review/pilot.html עם טבלת סיווגים וכל השאלות שחולצו.

שימוש:
    .venv/bin/python -I pipeline/build_review.py           (כל הבחינות ב-data/exams)
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, TAGS, TYPE_NAMES, UNITS, SUBTOPICS, exam_dirs, main_subtopic, parts, validate  # noqa: E402


def esc(text):
    return html.escape(text or "").replace("\n", "<br>")


def topic_label(sub_id):
    return SUBTOPICS[sub_id][1]["name"] if sub_id else "ללא תת-נושא בתוכנית"


def tag_badges(tags):
    return "".join(f'<span class="tag tag-{t}">{esc(TAGS[t])}</span>' for t in tags)


def figures_html(figs, rel):
    return "".join(f'<img class="fig" src="{rel}/figures/{f}" alt="">' for f in figs or [])


def item_html(p, rel):
    deps = p.get("depends_on") or []
    dep_html = (f'<span class="dep">תלוי בסעיף {", ".join(deps)}</span>'
                if deps else '<span class="indep">עצמאי</span>')
    table = ""
    if p.get("table"):
        t = p["table"]
        rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
                       for r in t["rows"])
        heads = "".join(f"<th>{esc(h)}</th>" for h in t["headers"])
        table = f"<table><tr>{heads}</tr>{rows}</table>"
    inter = p.get("interactive")
    inter_html = ""
    if inter:
        opts = inter.get("options")
        inter_html = ('<div class="inter">רכיב אינטראקטיבי: '
                      + (esc(" / ".join(opts)) if opts else '<b>אפשרויות חסרות</b>')
                      + (f" – {esc(inter['note'])}" if inter.get("note") else "") + "</div>")
    pts = f' <span class="pts">({p["points"]} נק\')</span>' if p.get("points") else ""
    note = f'<div class="note">⚠ {esc(p["review_note"])}</div>' if p.get("review_note") else ""
    return f"""
      <div class="item">
        <div class="item-head"><b>{esc(p['label'])}.</b>{pts} {dep_html}
          <span class="sub">({esc(topic_label(p.get('subtopic')))})</span> {tag_badges(p.get('tags', []))}</div>
        {f'<p class="intro">{esc(p["intro"])}</p>' if p.get('intro') else ''}
        {figures_html(p.get('figures'), rel)}
        {table}
        <p>{esc(p['text'])}</p>
        {inter_html}{note}
      </div>"""


def question_html(q, exam, passages, rel, problems):
    unit = UNITS[q["unit"]]["name"] if q.get("unit") else q.get("unit_note", "ללא יחידה בתוכנית")
    main = main_subtopic(q)
    body = ""
    if q.get("passage"):
        ps = passages[q["passage"]]
        body += (f'<details class="passage"><summary>אנסין: {esc(ps["title"])}</summary>'
                 f'<p class="intro">{esc(ps["intro"])}</p><p>{esc(ps["text"])}</p>'
                 f'<p class="credit">{esc(ps.get("credit", ""))}</p></details>')
    if q.get("stem"):
        body += f"<p>{esc(q['stem'])}</p>"
    if q["type"] == "mc":
        body += figures_html(q.get("figures"), rel)
        body += "<ol class='opts'>" + "".join(f"<li>{esc(o)}</li>" for o in q["options"]) + "</ol>"
        body += (f'<div class="item-head"><span class="sub">({esc(topic_label(q.get("subtopic")))})</span>'
                 f' {tag_badges(q.get("tags", []))}</div>')
    elif q["type"] == "tf":
        body += (f'<div class="item-head"><span class="sub">({esc(topic_label(q.get("subtopic")))})</span>'
                 f' {tag_badges(q.get("tags", []))}</div>')
    else:
        body += "".join(item_html(p, rel) for p in q["items"])
    if q.get("review_note"):
        body += f'<div class="note">⚠ {esc(q["review_note"])}</div>'
    if problems:
        body += '<div class="problem">' + "<br>".join(map(esc, problems)) + "</div>"
    return f"""
  <section class="q" id="{q['id']}">
    <div class="extracted">
      <header>
        <h2>{exam['year']} · שאלה {q['number']}</h2>
        <div class="meta">{esc(q.get('section', ''))} · {q['points']} נק' ·
          {TYPE_NAMES[q['type']]}</div>
        <div class="main">יחידה: <b>{esc(unit)}</b> · תת-נושא ראשי: <b>{esc(topic_label(main))}</b>
          {tag_badges(sorted({t for p in parts(q) for t in p.get('tags', [])}))}</div>
      </header>
      {body}
    </div>
  </section>"""


CSS = """
:root{--bg:#f6f7f4;--card:#fff;--ink:#1d2320;--mute:#5f6b64;--line:#dde2dc;--acc:#2f6f4f;
--warn:#8a5a00;--warnbg:#fff4dc;--bad:#a12a2a;--badbg:#fde8e8}
@media (prefers-color-scheme:dark){:root{--bg:#141816;--card:#1d2320;--ink:#e7ece8;--mute:#9aa69f;
--line:#2f3833;--acc:#7cc4a0;--warn:#f0c46a;--warnbg:#2e2614;--bad:#f19a9a;--badbg:#341a1a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 "Assistant","Arial Hebrew",Arial,sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:24px 16px}
h1{margin:0 0 4px}.lead{color:var(--mute);margin:0 0 24px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.stat b{display:block;font-size:22px}
.q{background:var(--card);
border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:20px}
.q h2{margin:0;font-size:20px}.meta{color:var(--mute);font-size:14px}
.main{margin:6px 0 12px;padding:8px 10px;background:var(--bg);border-radius:8px}
.item{border-top:1px solid var(--line);padding:10px 0}
.item-head{font-size:14px;margin-bottom:4px}.sub{color:var(--acc);font-weight:600}
.dep{color:var(--warn);font-size:13px;border:1px solid currentColor;border-radius:99px;padding:0 8px}
.indep{color:var(--mute);font-size:13px}
.intro{color:var(--mute)}.pts{color:var(--mute)}
.tag{font-size:12px;border-radius:99px;padding:1px 8px;margin-inline-start:4px;background:var(--bg);
border:1px solid var(--line)}.tag-old{color:var(--warn)}.tag-interactive{color:var(--acc)}
.fig{display:block;max-width:100%;max-height:340px;margin:8px 0;background:#fff;border-radius:6px}
.note{background:var(--warnbg);color:var(--warn);border-radius:8px;padding:6px 10px;margin:8px 0;font-size:14px}
.problem{background:var(--badbg);color:var(--bad);border-radius:8px;padding:6px 10px;margin:8px 0;font-size:14px}
.inter{font-size:14px;color:var(--acc)}
.opts{list-style:hebrew;padding-inline-start:28px}
table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid var(--line);padding:4px 10px}
.passage{background:var(--bg);border-radius:8px;padding:8px 12px;margin-bottom:10px}
.passage summary{cursor:pointer;font-weight:600}.credit{font-size:13px;color:var(--mute)}
.summary{overflow-x:auto;margin-bottom:32px}.summary table{width:100%;background:var(--card);font-size:14px}
.summary th{background:var(--bg);text-align:start}.summary td{vertical-align:top}
.summary tr:hover td{background:var(--bg);cursor:pointer}
"""


def summary_row(q, exam):
    """שורה בטבלת הסיכום: שאלה → יחידה → תת-נושא ראשי → תת-נושא לכל סעיף."""
    unit = UNITS[q["unit"]]["name"] if q.get("unit") else "—"
    if q["type"] in ("mc", "tf"):
        items = TYPE_NAMES[q["type"]]
    else:
        items = "<br>".join(
            f"{esc(p['label'])}: {esc(topic_label(p.get('subtopic')))}"
            + (f" ← {esc(', '.join(p['depends_on']))}" if p.get("depends_on") else "")
            for p in q["items"])
    tags = tag_badges(sorted({t for p in parts(q) for t in p.get("tags", [])}))
    return (f'<tr onclick="location.hash=\'{q["id"]}\'"><td>{exam["year"]} / {q["number"]}</td>'
            f"<td>{esc(unit)}</td><td><b>{esc(topic_label(main_subtopic(q)))}</b></td>"
            f"<td>{items}</td><td>{tags}</td></tr>")


def main(dirs):
    sections, rows, n_q, n_items, n_problems = [], [], 0, 0, 0
    for d in dirs:
        data = json.loads((d / "questions.json").read_text(encoding="utf-8"))
        passages = {p["id"]: p for p in data["passages"]}
        rel = "../" + d.relative_to(ROOT).as_posix()
        for q in data["questions"]:
            problems = validate(q, d)
            n_q += 1
            n_items += len(parts(q))
            n_problems += len(problems)
            sections.append(question_html(q, data["exam"], passages, rel, problems))
            rows.append(summary_row(q, data["exam"]))
            print(f"{q['id']:10} unit={q.get('unit')} main={main_subtopic(q)} problems={len(problems)}")

    page = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>פיילוט חילוץ</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>פיילוט חילוץ שאלות – בדיקה</h1>
<p class="lead">לכל שאלה: יחידה, תת-נושא ראשי, תת-נושא לכל סעיף, תלות בין סעיפים ותגיות.</p>
<div class="stats"><div class="stat"><b>{n_q}</b>שאלות</div><div class="stat"><b>{n_items}</b>סעיפים</div>
<div class="stat"><b>{n_problems}</b>בעיות פתוחות</div></div>
<h2>טבלת סיווגים</h2>
<p class="lead">לחיצה על שורה קופצת לשאלה. ← = הסעיף תלוי בסעיף שמצוין.</p>
<div class="summary"><table><tr><th>שנה / שאלה</th><th>יחידה</th><th>תת-נושא ראשי</th>
<th>תת-נושא לכל סעיף</th><th>תגיות</th></tr>{''.join(rows)}</table></div>
<h2>השאלות</h2>
{''.join(sections)}
</div></body></html>"""
    out = ROOT / "review/pilot.html"
    out.write_text(page, encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main(exam_dirs(sys.argv[1:]))
