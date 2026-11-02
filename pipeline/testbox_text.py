"""המרת עמוד שאלות של testbox (HTML סטטי) לטקסט קריא עם סימונים.

שימוש:
    .venv/bin/python -I pipeline/testbox_text.py raw/testbox/2023/question1-2.htm

הסימונים בפלט:
    [[א | ב | ג]]     רשימה נפתחת (האפשרויות כפי שהן בעמוד)
    ( )               כפתור בחירה (אמריקאית / נכון–לא נכון)
    [____]            תיבת תשובה פתוחה
    {{IMG שם}}        איור
    {{VIDEO שם}}      אנימציה
    ¦                 גבול בין תאים בטבלה
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "table", "ul", "ol"}
SKIP = {"script", "style", "noscript"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = []          # מחסנית תגים שמדלגים על תוכנם
        self.select = None      # אפשרויות הרשימה הנפתחת הנוכחית
        self.option = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if self.skip:
            if tag not in ("br", "img", "input", "source", "meta", "link"):
                self.skip.append(tag)
            return
        if tag in SKIP or "advancedrecorder" in cls or cls.startswith("ar-") or "btn_tooltip" in cls:
            self.skip.append(tag)
            return
        if tag == "select":
            self.select = []
        elif tag == "option" and self.select is not None:
            self.option = ""
        elif tag == "img":
            src = a.get("src") or ""
            if "myimg" in src or src.lower().endswith((".png", ".jpg", ".gif")) and "/img/" not in src:
                self.out.append(" {{IMG %s}} " % src.rsplit("/", 1)[-1])
        elif tag == "source":
            src = a.get("src") or ""
            if src.endswith(".mp4"):
                self.out.append(" {{VIDEO %s}} " % src.rsplit("/", 1)[-1])
        elif tag == "input" and a.get("type") in ("radio", "checkbox"):
            self.out.append("( ) ")
        elif tag == "textarea":
            self.out.append("\n[____]\n")
            self.skip.append(tag)
        elif tag in ("td", "th"):
            self.out.append(" ¦ ")
        if tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if self.skip:
            self.skip.pop()
            return
        if tag == "option" and self.option is not None:
            t = self.option.strip()
            if t:
                self.select.append(t)
            self.option = None
        elif tag == "select" and self.select is not None:
            self.out.append(" [[" + " | ".join(self.select) + "]] ")
            self.select = None
        if tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.option is not None:
            self.option += data
        elif self.select is None:
            self.out.append(data)


def convert(path):
    p = Text()
    p.feed(Path(path).read_text(encoding="utf-8-sig"))
    s = "".join(p.out).replace("\xa0", " ")
    s = re.sub(r"[‎‏‪-‮]", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    # מדלגים על כותרות הניווט שבראש העמוד ובסופו
    i = s.find("ניווט")
    m = re.search(r"\nשאלה \d+\n", s)
    start = m.start() if m else 0
    end = s.find("ניווט", start)
    return s[start:end if end > 0 else None].strip() + "\n"


if __name__ == "__main__":
    for f in sys.argv[1:]:
        out = Path(f).with_suffix(".txt")
        out.write_text(convert(f), encoding="utf-8")
        print(out)
