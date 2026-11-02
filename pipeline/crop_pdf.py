"""חיתוך ידני של איורים מה-PDF, כשהחיתוך האוטומטי של extract_pdf.py לא מדויק.

שימוש:
    .venv/bin/python -I pipeline/crop_pdf.py raw/pdf/2016.pdf data/exams/2016

קובץ crops_pdf.json בתיקיית הבחינה – רשימה של:
    {"page": 19, "out": "p19_f1.png",
     "top": "<קטע משורה שהאיור מתחיל מתחתיה>" או מספר (נקודות PDF),
     "bottom": "<קטע משורה שהאיור נגמר מעליה>" או מספר,
     "x": [x0, x1]}                     # אופציונלי; ברירת מחדל – כל רוחב הטקסט
    "remove": ["p19_f2.png"]             # (ברמת הקובץ) איורים אוטומטיים למחיקה
הטקסט מחופש בשורות כפי שהן מופיעות ב-text.txt.
"""
import json
import sys
from pathlib import Path

import fitz

HEADER_H, FOOTER_H, MARGIN, PAD, DPI = 70, 50, 36, 4, 200


def lines(page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            yield "".join(s["text"] for s in line["spans"]), fitz.Rect(line["bbox"])


def find(page, needle):
    for text, rect in lines(page):
        if needle in text:
            return rect
    raise SystemExit(f"עמוד {page.number + 1}: לא נמצאה שורה עם '{needle}'")


def edge(page, spec, default, top):
    if spec is None:
        return default
    if isinstance(spec, (int, float)):
        return spec
    r = find(page, spec)
    return r.y1 + PAD if top else r.y0 - PAD


def main(pdf, exam_dir):
    exam = Path(exam_dir)
    spec = json.loads((exam / "crops_pdf.json").read_text(encoding="utf-8"))
    doc = fitz.open(pdf)
    for name in spec.get("remove", []):
        (exam / "figures" / name).unlink(missing_ok=True)
    for c in spec["crops"]:
        page = doc[c["page"] - 1]
        w, h = page.rect.width, page.rect.height
        y0 = edge(page, c.get("top"), HEADER_H, True)
        y1 = edge(page, c.get("bottom"), h - FOOTER_H, False)
        x0, x1 = c.get("x", [MARGIN, w - MARGIN])
        page.get_pixmap(clip=fitz.Rect(x0, y0, x1, y1), dpi=DPI).save(exam / "figures" / c["out"])
        print(c["out"], [round(v) for v in (x0, y0, x1, y1)])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
