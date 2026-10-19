import unittest

from contribution_summary import summary

TEXT = {
    "sections": {"Pull requests": "PR", "Issues": "Issues", "Commits": "Коммиты"},
    "states": {
        "Pull requests": {"done": "принято", "open": "открыто"},
        "Issues": {"done": "выполнено", "open": "открыто"},
        "Commits": {"done": "принято", "open": "открыто"},
    },
}


class SummaryTest(unittest.TestCase):
    def test_mixed_counts(self):
        project = {"sections": [
            {"title": "Pull requests", "items": [{"state": "done"}, {"state": "open"}]},
            {"title": "Issues", "items": [{"state": "done"}]},
        ]}
        self.assertEqual(summary(project, TEXT), "PR: 1 принято, 1 открыто · Issues: 1 выполнено")

    def test_single_commit_section(self):
        project = {"sections": [{"title": "Commits", "items": [{"state": "done"}]}]}
        self.assertEqual(summary(project, TEXT), "Коммиты: 1 принято")

    def test_empty_legacy_sections_are_omitted(self):
        project = {"sections": [
            {"title": "Pull requests", "items": []},
            {"title": "Issues", "items": [{"state": "open"}]},
        ]}
        self.assertEqual(summary(project, TEXT), "Issues: 1 открыто")


if __name__ == "__main__":
    unittest.main()
