#!/usr/bin/env python3
"""Build ATS-friendly cv-<lang>.pdf files from content.json and contributions.json."""
import datetime
import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from contribution_summary import summary

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

FULL_LIST_URL = "https://ashm-dev.github.io/"


def plural(n, forms):
    if n % 10 == 1 and n % 100 != 11:
        form = "one"
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        form = "few"
    else:
        form = "many"
    return forms[form].replace("{n}", str(n))


def months_between(start, end):
    year1, month1 = (int(part) for part in start.split("-"))
    if end:
        year2, month2 = (int(part) for part in end.split("-"))
    else:
        today = datetime.date.today()
        year2, month2 = today.year, today.month
    return max(1, year2 * 12 + month2 - (year1 * 12 + month1) + 1)


def years_since(since, forms):
    return plural(max(1, months_between(since, None) // 12), forms)


def duration(job, forms):
    months = months_between(job["start"], job["end"])
    parts = []
    if months >= 12:
        parts.append(plural(months // 12, forms["year"]))
    if months % 12:
        parts.append(plural(months % 12, forms["month"]))
    return " ".join(parts)


def register_fonts():
    pdfmetrics.registerFont(TTFont("JBMono", str(FONTS / "JetBrainsMono-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("JBMono-Bold", str(FONTS / "JetBrainsMono-Bold.ttf")))


def styles():
    base = ParagraphStyle("base", fontName="JBMono", fontSize=8.5, leading=10.5)
    muted = ParagraphStyle("muted", parent=base, textColor="#555555")
    return {
        "name": ParagraphStyle("name", parent=base, fontName="JBMono-Bold", fontSize=15, leading=18, spaceAfter=2),
        "h2": ParagraphStyle("h2", parent=base, fontName="JBMono-Bold", fontSize=10.5, leading=14, spaceBefore=10, spaceAfter=2),
        "body": base,
        "muted": muted,
        "oss_intro": ParagraphStyle("oss_intro", parent=base, spaceAfter=4),
        "oss_item": ParagraphStyle("oss_item", parent=base, leftIndent=0, firstLineIndent=0, spaceAfter=1.5),
        "job": ParagraphStyle("job", parent=base, keepWithNext=True, spaceBefore=2),
        "period": ParagraphStyle("period", parent=muted, keepWithNext=True, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=10, firstLineIndent=-10, spaceAfter=2),
    }


def heading(text, st):
    return [Paragraph(esc(text), st["h2"]), HRFlowable(width="100%", thickness=0.6, color="#bbbbbb", spaceAfter=4)]


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def link(url, label):
    return f'<link href="{esc(url)}">{esc(label)}</link>'


def profile_blocks(t, since, projects, st):
    blocks = [Paragraph(esc(t["name"]), st["name"]), Paragraph(esc(t["role"]), st["muted"]), Spacer(1, 8)]
    contacts = [link(FULL_LIST_URL, FULL_LIST_URL.removeprefix("https://").rstrip("/"))]
    contacts += [link(c["url"], c["url"].removeprefix("mailto:") if c["url"].startswith("mailto:") else c["label"]) for c in t["contacts"]]
    blocks.append(Paragraph(" · ".join(contacts), st["muted"]))
    summary_text = t["summary"].replace("{years}", years_since(since, t["years"]))
    blocks += [Spacer(1, 8), Paragraph(esc(summary_text), st["body"])]
    blocks += oss_blocks(projects, t, st)
    blocks += heading(t["headings"]["experience"], st)
    for job in t["experience"]:
        blocks.append(Paragraph(f"<b>{esc(job['title'])}</b>, {link(job['url'], job['company'])}", st["job"]))
        blocks.append(Paragraph(f"{esc(job['period'])} · {esc(duration(job, t['duration']))}", st["period"]))
        blocks += [Paragraph(f"• {esc(b)}", st["bullet"]) for b in job["bullets"]]
        blocks.append(Spacer(1, 5))
    blocks += heading(t["headings"]["languages"], st)
    blocks.append(Paragraph(" · ".join(esc(lang_item["text"]) for lang_item in t["languages"]), st["body"]))
    return blocks


def oss_blocks(projects, t, st):
    blocks = heading(t["headings"]["oss"], st)
    blocks.append(Paragraph(esc(t["oss_summary"]), st["oss_intro"]))
    blocks += [Paragraph(f"<b>{esc(project['name'])}</b> — {esc(summary(project, t))}", st["oss_item"]) for project in projects]
    return blocks + [Spacer(1, 2)]


def build(lang, content, projects, out):
    st = styles()
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=content[lang]["name"], author=content["en"]["name"])
    doc.build(profile_blocks(content[lang], content["since"], projects, st))


def main(contributions_path, output_dir=ROOT):
    register_fonts()
    content = json.loads((ROOT / "content.json").read_text())
    projects = json.loads(Path(contributions_path).read_text())
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "ru"):
        build(lang, content, projects, output_dir / f"cv-{lang}.pdf")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ROOT)
