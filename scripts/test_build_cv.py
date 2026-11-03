import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reportlab.platypus import Paragraph, SimpleDocTemplate

from build_cv import ROOT, build, main, register_fonts


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

    def test_open_source_is_the_first_experience_entry_in_both_languages(self):
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
                with patch("build_cv.SimpleDocTemplate") as document:
                    build(lang, content, projects, "unused.pdf")
                blocks = document.return_value.build.call_args.args[0]
                text = [block.getPlainText() for block in blocks if isinstance(block, Paragraph)]
                experience = text.index(content[lang]["headings"]["experience"])
                job = content[lang]["experience"][0]
                company = f"{job['title']}, {job['company']}"
                self.assertEqual(text[experience + 1:experience + 5], ["OpenSource", *summaries, company])
                self.assertTrue(text[text.index(company) + 1].startswith(period + " · "))
                self.assertEqual(text.count("OpenSource"), 1)
                for line in summaries:
                    self.assertEqual(text.count(line), 1)

    def test_employment_headers_stay_with_the_first_bullet(self):
        register_fonts()
        content = json.loads((ROOT / "content.json").read_text())
        projects = [{
            "name": name,
            "sections": [{"title": section, "items": [{"state": "done"} for _ in range(6)]}],
        } for name, section in [
            ("python/cpython", "Pull requests"), ("glibc", "Patches"),
            ("python/typeshed", "Pull requests"), ("open-webui/open-webui", "Pull requests"),
        ]]
        pages = {}

        def document(*args, **kwargs):
            doc = SimpleDocTemplate(*args, **kwargs)
            doc.afterFlowable = lambda block: pages.setdefault(block.getPlainText(), doc.page) if isinstance(block, Paragraph) else None
            return doc

        with tempfile.TemporaryDirectory() as directory:
            with patch("build_cv.SimpleDocTemplate", side_effect=document):
                build("ru", content, projects, Path(directory) / "cv.pdf")
        for job in content["ru"]["experience"]:
            company = f"{job['title']}, {job['company']}"
            first_bullet = f"• {job['bullets'][0]['lead']}: {job['bullets'][0]['text']}"
            self.assertEqual(pages[company], pages[first_bullet], company)

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
