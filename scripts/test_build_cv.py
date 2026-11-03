import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from build_cv import FULL_LIST_URL, ROOT, build, main, profile_blocks, register_fonts, styles


class BuildCVTest(unittest.TestCase):
    def test_builds_both_pdfs_in_the_artifact_without_changing_tracked_files(self):
        tracked = [ROOT / f"cv-{lang}.pdf" for lang in ("en", "ru")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "contributions.json"
            source.write_text(json.dumps([{
                "name": "python/cpython",
                "sections": [{"title": "Pull requests", "items": [{"state": "done"}]}],
            }]))
            output = root / "site"
            main(source, output)
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["cv-en.pdf", "cv-ru.pdf"])
            for lang in ("en", "ru"):
                pdf = (output / f"cv-{lang}.pdf").read_bytes()
                self.assertTrue(pdf.startswith(b"%PDF-"))
                self.assertGreater(len(pdf), 1000)
        self.assertEqual([hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked], before)

    def test_contacts_share_one_compact_linked_paragraph(self):
        register_fonts()
        content = json.loads((ROOT / "content.json").read_text())
        for lang in ("en", "ru"):
            with self.subTest(lang=lang):
                blocks = profile_blocks(content[lang], content["since"], [], styles())
                paragraphs = [block for block in blocks if isinstance(block, Paragraph)]
                contacts = paragraphs[2]
                self.assertEqual(contacts.getPlainText(), "ashm-dev.github.io · GitHub · LinkedIn · Telegram · ashamil435@gmail.com")
                self.assertEqual([target for fragment in contacts.frags for _, target in fragment.link], [
                    FULL_LIST_URL, "https://github.com/ashm-dev", "https://www.linkedin.com/in/ashm-tech/",
                    "https://t.me/ashamil435", "mailto:ashamil435@gmail.com",
                ])
                self.assertIsInstance(blocks[blocks.index(contacts) + 1], Spacer)
                self.assertEqual(blocks[blocks.index(contacts) + 1].height, 8)
                self.assertIs(paragraphs[3], blocks[blocks.index(contacts) + 2])

    def test_open_source_section_precedes_commercial_experience_in_both_languages(self):
        register_fonts()
        content = json.loads((ROOT / "content.json").read_text())
        projects = [
            {"name": "python/cpython", "sections": [{"title": "Pull requests", "items": [{"state": "done"} for _ in range(6)]}]},
            {"name": "glibc", "sections": [{"title": "Patches", "items": [{"state": "done"} for _ in range(6)]}]},
        ]
        for lang, summaries, period in [
            ("en", ["python/cpython — PR: 6 merged", "glibc — Patches: 6 committed"], "Nov 2023 — Nov 2026"),
            ("ru", ["python/cpython — PR: 6 принято", "glibc — Патчи: 6 принято"], "ноя 2023 — ноя 2026"),
        ]:
            with self.subTest(lang=lang):
                t = {**content[lang], "summary": "Profile summary.", "oss_summary": "Core runtime contributions."}
                blocks = profile_blocks(t, content["since"], projects, styles())
                paragraphs = [block for block in blocks if isinstance(block, Paragraph)]
                text = [block.getPlainText() for block in paragraphs]
                experience = text.index(t["headings"]["experience"])
                job = t["experience"][0]
                company = f"{job['title']}, {job['company']}"
                self.assertEqual(text[experience - 4:experience], [t["headings"]["oss"], "Core runtime contributions.", *summaries])
                self.assertEqual(text[experience + 1], company)
                self.assertTrue(text[text.index(company) + 1].startswith(period + " · "))
                self.assertEqual(text.count(t["headings"]["oss"]), 1)
                self.assertEqual(paragraphs[experience - 4].style.name, "h2")
                self.assertEqual(text[experience - 5], "Profile summary.")
                self.assertEqual(paragraphs[experience - 3].getSpaceAfter(), 4)
                for item in paragraphs[experience - 2:experience]:
                    self.assertEqual(item.getSpaceAfter(), 1.5)
                for line in summaries:
                    self.assertEqual(text.count(line), 1)

    def test_experience_bullets_are_plain_text_in_both_languages(self):
        register_fonts()
        content = json.loads((ROOT / "content.json").read_text())
        for lang in ("en", "ru"):
            with self.subTest(lang=lang):
                t = content[lang]
                bullets = [bullet for job in t["experience"] for bullet in job["bullets"]]
                for bullet in bullets:
                    self.assertIsInstance(bullet, str)
                blocks = profile_blocks(t, content["since"], [], styles())
                rendered = [block for block in blocks if isinstance(block, Paragraph) and block.style.name == "bullet"]
                self.assertEqual([block.getPlainText() for block in rendered], [f"• {bullet}" for bullet in bullets])
                for block in rendered:
                    self.assertNotIn("<b>", block.text)

    def test_both_resumes_fit_one_page_without_splitting_employment(self):
        register_fonts()
        content = json.loads((ROOT / "content.json").read_text())
        projects = [{
            "name": name,
            "sections": [{
                "title": title,
                "items": [{"state": state} for state, count in [("done", done), ("open", opened)] for _ in range(count)],
            } for title, done, opened in sections],
        } for name, sections in [
            ("python/cpython", [("Pull requests", 35, 2), ("Issues", 31, 16)]),
            ("glibc", [("Patches", 12, 5), ("Bugs", 2, 5)]),
            ("python/typeshed", [("Pull requests", 10, 0)]),
            ("sqlalchemy/sqlalchemy", [("Commits", 10, 0), ("Issues", 6, 1)]),
            ("open-webui/open-webui", [("Pull requests", 8, 0), ("Issues", 6, 0)]),
        ]]
        for lang in ("en", "ru"):
            with self.subTest(lang=lang):
                pages = {}
                documents = []

                def document(*args, **kwargs):
                    doc = SimpleDocTemplate(*args, **kwargs)
                    doc.afterFlowable = lambda block: pages.setdefault(block.getPlainText(), doc.page) if isinstance(block, Paragraph) else None
                    documents.append(doc)
                    return doc

                with tempfile.TemporaryDirectory() as directory:
                    with patch("build_cv.SimpleDocTemplate", side_effect=document):
                        build(lang, content, projects, Path(directory) / "cv.pdf")
                self.assertEqual(documents[0].page, 1)
                for job in content[lang]["experience"]:
                    company = f"{job['title']}, {job['company']}"
                    for bullet in job["bullets"]:
                        self.assertEqual(pages[company], pages[f"• {bullet}"], company)
                for project in projects:
                    self.assertTrue(any(text.startswith(project["name"] + " — ") for text in pages), project["name"])

    def test_invalid_data_does_not_produce_a_publishable_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "contributions.json"
            source.write_text("not JSON")
            output = root / "site"
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/build_cv.py"), str(source), str(output)],
                capture_output=True, timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
