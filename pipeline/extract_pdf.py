"""חילוץ טקסט, תמונות עמודים ואיורים מקובץ PDF של בחינת בגרות.

שימוש:
    .venv/bin/python -I pipeline/extract_pdf.py raw/pdf/2010.pdf data/exams/2010

פלט:
    pages/pNN.png        – צילום של כל עמוד (לבדיקה מול המקור)
    figures/pNN_fK.png   – איורים שזוהו (אשכולות של גרפיקה וקטורית / תמונות)
    figures.json         – מיקום כל איור בעמוד
    text.txt             – הטקסט הגולמי, עמוד אחר עמוד
"""
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

HEADER_H = 70      # שוליים עליונים: כותרת העמוד ("- 3 -", סמל שאלון)
FOOTER_H = 50      # שוליים תחתונים: "המשך בעמוד"
GAP = 18           # מרחק אנכי מקסימלי בין רכיבים של אותו איור
PAD = 22           # הרחבת האיור כדי לכלול תוויות טקסט סביב הגרפיקה
MIN_H, MIN_W = 30, 40


def graphic_rects(page):
    """מלבנים של כל הגרפיקה בעמוד, בלי קווי הכותרת והשוליים."""
    h = page.rect.height
    rects = [d["rect"] for d in page.get_drawings()]
    rects += [page.get_image_bbox(img) for img in page.get_images(full=True)]
    # קו ישר הוא מלבן בגובה/רוחב אפס – לכן לא מסננים לפי is_empty
    return [r for r in rects
            if r.y0 > HEADER_H and r.y1 < h - FOOTER_H
            and (r.width > 0 or r.height > 0)]


def cluster(rects):
    """איחוד מלבנים קרובים אנכית לאשכולות = איורים."""
    groups = []
    for r in sorted(rects, key=lambda r: r.y0):
        if groups and r.y0 - groups[-1].y1 < GAP:
            groups[-1] |= r
        else:
            groups.append(fitz.Rect(r))
    return [g for g in groups if g.height >= MIN_H and g.width >= MIN_W]


def label_lines(page):
    """שורות טקסט קצרות – תוויות צירים, כותרות איור, מספרי מסלולים.
    שורות ארוכות הן טקסט השאלה ולא חלק מהאיור."""
    max_w = page.rect.width * 0.55
    all_lines = [fitz.Rect(line["bbox"])
                 for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", [])]
    # שוליים ימניים של הטקסט הרץ (עברית מיושרת לימין; לסעיפים יש הזחה משלהם) –
    # שורה קצרה שמסתיימת באחד השוליים האלה היא סוף פסקה ולא תווית
    margins = {round(r.x1) for r in all_lines if r.width >= max_w}
    return [r for r in all_lines if r.width < max_w
            and all(abs(r.x1 - m) > 4 for m in margins)]


def grow_with_labels(box, labels):
    """הרחבת האיור כך שיכלול תוויות שנוגעות בו או צמודות אליו."""
    changed = True
    while changed:
        changed = False
        near = box + (-PAD, -PAD, PAD, PAD)
        for r in labels:
            if near.intersects(r) and not box.contains(r):
                box |= r
                changed = True
    return box


def main(pdf_path, out_dir):
    out = Path(out_dir)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    doc = fitz.open(pdf_path)
    figures, text = [], []

    for i, page in enumerate(doc, start=1):
        page.get_pixmap(dpi=110).save(out / "pages" / f"p{i:02d}.png")
        text.append(f"\n===== PAGE {i} =====\n{page.get_text()}")
        labels = label_lines(page)
        for k, box in enumerate(cluster(graphic_rects(page)), start=1):
            box = grow_with_labels(box, labels)
            clip = (box + (-6, -6, 6, 6)) & page.rect
            name = f"p{i:02d}_f{k}.png"
            page.get_pixmap(dpi=200, clip=clip).save(out / "figures" / name)
            figures.append({"file": name, "page": i,
                            "bbox": [round(v, 1) for v in clip]})

    (out / "text.txt").write_text("".join(text), encoding="utf-8")
    (out / "figures.json").write_text(
        json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{doc.page_count} pages, {len(figures)} figures -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
