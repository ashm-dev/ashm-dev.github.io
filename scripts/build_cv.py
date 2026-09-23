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

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
DONE = "done"

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
    base = ParagraphStyle("base", fontName="JBMono", fontSize=10, leading=15)
    return {
        "name": ParagraphStyle("name", parent=base, fontName="JBMono-Bold", fontSize=18, leading=22),
        "h2": ParagraphStyle("h2", parent=base, fontName="JBMono-Bold", fontSize=12, leading=16, spaceBefore=16, spaceAfter=2),
        "body": base,
        "muted": ParagraphStyle("muted", parent=base, textColor="#555555"),
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=12, firstLineIndent=-12, spaceAfter=2),
    }


def heading(text, st):
    return [Paragraph(esc(text), st["h2"]), HRFlowable(width="100%", thickness=0.6, color="#bbbbbb", spaceAfter=6)]


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def link(url, label):
    return f'<link href="{esc(url)}">{esc(label)}</link>'


def landed(section):
    return sum(1 for item in section["items"] if item["state"] == DONE)


def summary(project, t):
    first, second = project["sections"]
    verb = t["verbs"].get(first["title"], t["verbs"]["Pull requests"])
    return f"{landed(first)} {verb} {t['nouns'][first['title']]} · {len(second['items'])} {t['nouns'][second['title']]}"


def profile_blocks(t, since, st):
    blocks = [Paragraph(esc(t["name"]), st["name"]), Paragraph(esc(t["role"]), st["muted"]), Spacer(1, 8)]
    blocks.append(Paragraph(f"{esc(t['site_label'])}: {link(FULL_LIST_URL, FULL_LIST_URL)}", st["body"]))
    blocks += [Paragraph(f"{esc(c['label'])}: {link(c['url'], c['url'].removeprefix('mailto:'))}", st["body"]) for c in t["contacts"]]
    summary_text = t["summary"].replace("{years}", years_since(since, t["years"]))
    blocks += [Spacer(1, 12), Paragraph(esc(summary_text), st["body"])]
    blocks += heading(t["headings"]["experience"], st)
    for job in t["experience"]:
        blocks.append(Paragraph(f"<b>{esc(job['title'])}</b>, {link(job['url'], job['company'])}", st["body"]))
        blocks.append(Paragraph(f"{esc(job['period'])} · {esc(duration(job, t['duration']))}", st["muted"]))
        blocks.append(Spacer(1, 3))
        blocks += [Paragraph(f"• <b>{esc(b['lead'])}:</b> {esc(b['text'])}", st["bullet"]) for b in job["bullets"]]
        blocks.append(Spacer(1, 8))
    blocks += heading(t["headings"]["languages"], st)
    blocks += [Paragraph(esc(lang_item["text"]), st["body"]) for lang_item in t["languages"]]
    return blocks


def oss_blocks(projects, t, st):
    blocks = heading(t["headings"]["oss"], st)
    blocks += [Paragraph(esc(t["oss_pdf_note"]), st["muted"]), Spacer(1, 6)]
    blocks += [Paragraph(f"<b>{esc(project['name'])}</b> — {esc(summary(project, t))}", st["body"]) for project in projects]
    return blocks


def build(lang, content, projects, out):
    st = styles()
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                            title=content[lang]["name"], author=content["en"]["name"])
    doc.build(profile_blocks(content[lang], content["since"], st) + oss_blocks(projects, content[lang], st))


def main(contributions_path):
    register_fonts()
    content = json.loads((ROOT / "content.json").read_text())
    projects = json.loads(Path(contributions_path).read_text())
    for lang in ("en", "ru"):
        build(lang, content, projects, ROOT / f"cv-{lang}.pdf")


if __name__ == "__main__":
    main(sys.argv[1])
