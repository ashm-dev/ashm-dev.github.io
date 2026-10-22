import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from build_cv import ROOT, main


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
