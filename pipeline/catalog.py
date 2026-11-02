"""לוגיקה משותפת לסקריפטים: עץ הנושאים, תת-נושא ראשי ובדיקות עקביות."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = json.loads((ROOT / "data/topics.json").read_text(encoding="utf-8"))
UNITS = {u["id"]: u for u in TOPICS["units"]}
SUBTOPICS = {s["id"]: (u["id"], s) for u in TOPICS["units"] for s in u["subtopics"]}
TAGS = {t["id"]: t["name"] for t in TOPICS["tags"]}


TYPE_NAMES = {"mc": "אמריקאית", "tf": "נכון / לא נכון", "open": "פתוחה"}


def parts(q):
    """שאלה אמריקאית היא 'סעיף' יחיד; שאלה פתוחה – רשימת הסעיפים שלה."""
    return q.get("items") or [q]


def main_subtopic(q):
    """תת-הנושא המתקדם ביותר (order גבוה) מבין הסעיפים, בתוך יחידת השאלה.
    בתיקיית 'נושאים קודמים' נספרים רק סעיפים מהתיקייה עצמה."""
    found = [SUBTOPICS[p["subtopic"]] for p in parts(q) if p.get("subtopic")]
    found = [s for unit, s in found if unit == q["unit"]]
    return max(found, key=lambda s: s["order"])["id"] if found else None


def validate(q, exam_dir):
    problems = []
    labels = {p.get("label") for p in parts(q)}
    allowed = {q["unit"]}
    if q["unit"] == "OLD" and q.get("origin_unit"):
        allowed.add(q["origin_unit"])
    for p in parts(q):
        sub = p.get("subtopic")
        if sub and SUBTOPICS[sub][0] not in allowed:
            problems.append(f"סעיף {p.get('label', '')}: תת-נושא {sub} לא מהיחידה {q['unit']}")
        for dep in p.get("depends_on", []):
            if dep not in labels:
                problems.append(f"סעיף {p['label']} תלוי בסעיף לא קיים {dep}")
        for fig in p.get("figures", []):
            if not (exam_dir / "figures" / fig).exists():
                problems.append(f"איור חסר: {fig}")
        if (p.get("interactive") or {}).get("options", "") is None:
            problems.append(f"סעיף {p['label']}: חסרות אפשרויות לרשימה הנפתחת")
    for fig in q.get("stem_figures", []):
        if not (exam_dir / "figures" / fig).exists():
            problems.append(f"איור חסר: {fig}")
    if q["type"] == "mc" and len(q.get("options", [])) < 2:
        problems.append("שאלה אמריקאית בלי אפשרויות")
    if q["type"] == "open" and not q.get("items"):
        problems.append("שאלה פתוחה בלי סעיפים")
    if q["type"] == "tf" and (q.get("items") or q.get("options")):
        problems.append("שאלת נכון/לא נכון עם סעיפים או אפשרויות")
    return problems


def exam_dirs(args):
    """תיקיות הבחינות: מהארגומנטים, או כל מה שיש ב-data/exams עם questions.json."""
    if args:
        return [Path(a).resolve() for a in args]
    return sorted(p for p in (ROOT / "data/exams").iterdir() if (p / "questions.json").exists())
