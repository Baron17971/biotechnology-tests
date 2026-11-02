"""גיליון תמונות מוקטנות של כל האיורים שחולצו מבחינה – לבדיקה מהירה של החיתוך והשיוך.

שימוש:
    .venv/bin/python -I pipeline/contact_sheet.py data/exams/2016 out.png
"""
import sys
from pathlib import Path

import fitz

CELL_W, CELL_H, LABEL_H, COLS = 300, 220, 18, 4


def main(exam_dir, out):
    figs = sorted((Path(exam_dir) / "figures").glob("*.png"))
    rows = (len(figs) + COLS - 1) // COLS
    doc = fitz.open()
    page = doc.new_page(width=CELL_W * COLS, height=(CELL_H + LABEL_H) * rows)
    for i, f in enumerate(figs):
        x, y = (i % COLS) * CELL_W, (i // COLS) * (CELL_H + LABEL_H)
        page.insert_text((x + 6, y + 13), f.name, fontsize=11)
        page.insert_image(fitz.Rect(x + 4, y + LABEL_H, x + CELL_W - 4, y + LABEL_H + CELL_H - 4),
                          filename=str(f), keep_proportion=True)
        page.draw_rect(fitz.Rect(x + 2, y + 2, x + CELL_W - 2, y + LABEL_H + CELL_H - 2), color=(0.7, 0.7, 0.7))
    page.get_pixmap(dpi=72).save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
