"""חיתוך איורים מצילומי מסך של testbox לפי קובץ הגדרות.

שימוש:
    .venv/bin/python -I pipeline/crop_figures.py data/exams/2024

קובץ crops.json בתיקיית הבחינה:
    {"frame": [666, 1000],                       # גודל מסגרת הקואורדינטות של הצילום
     "crops": [{"src": "pages/s05.jpg", "out": "q3_fig_a.png", "box": [x0, y0, x1, y1]}, ...]}
"""
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF – משמש גם לחיתוך תמונות רגילות


def crop(src, dst, box, frame):
    pix = fitz.Pixmap(str(src))
    sx, sy = pix.width / frame[0], pix.height / frame[1]
    doc = fitz.open()
    page = doc.new_page(width=pix.width, height=pix.height)
    page.insert_image(page.rect, filename=str(src))
    clip = fitz.Rect(box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy)
    page.get_pixmap(clip=clip, dpi=144).save(str(dst))


def main(exam_dir):
    exam = Path(exam_dir)
    spec = json.loads((exam / "crops.json").read_text(encoding="utf-8"))
    (exam / "figures").mkdir(exist_ok=True)
    for c in spec["crops"]:
        crop(exam / c["src"], exam / "figures" / c["out"], c["box"],
             c.get("frame", spec["frame"]))
        print(c["out"])


if __name__ == "__main__":
    main(sys.argv[1])
