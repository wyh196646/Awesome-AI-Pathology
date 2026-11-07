import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("arxiv_html", ROOT / "scripts/search_arxiv_html.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def entry(identifier="2301.00001", version=2):
    return f'''<li class="arxiv-result"><p class="title">A histology model</p>
      <p class="authors"><a>Alice Example</a></p>
      <span class="abstract-full" id="{identifier}v{version}-abstract-full">
      Beginning <span class="search-hit">tissue</span> images and the complete ending.
      <a>△ Less</a></span><p>Submitted 12 October, 2026;</p></li>'''


class ArxivHTMLTests(unittest.TestCase):
    def test_explicit_official_zero_result_is_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "empty.json"
            arguments = ["search_arxiv_html.py", "--since", "2023-01-01", "--until", "2023-12-31",
                         "--cache-dir", directory, "--output", str(destination)]
            with patch.object(module, "CACHE", Path(directory)), \
                    patch.object(module, "fetch", return_value="Sorry, your query returned no results"), \
                    patch.object(sys, "argv", arguments), contextlib.redirect_stdout(io.StringIO()):
                result = module.main()
            data = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        self.assertEqual(data["source_status"]["arxiv"]["status"], "complete")
        self.assertEqual(data["retrievals"][0]["total"], 0)

    def test_nested_search_highlights_do_not_truncate_abstract_or_invent_first_date(self):
        record = module.parse(entry(), "https://arxiv.org/search/")[0]
        self.assertEqual(record["abstract"], "Beginning tissue images and the complete ending.")
        self.assertEqual(record["version"], 2)
        self.assertEqual(record["updated"], "2026-10-12")
        self.assertIsNone(record["first_posted"])
        self.assertTrue(record["first_posted_requires_history"])
        self.assertEqual(record["paper_url"], "https://arxiv.org/abs/2301.00001v2")

    def test_pagination_limit_retains_partial_records_but_marks_source_failed(self):
        raw = "Showing 1–200 of 201 results" + "".join(
            entry(f"2301.{i:05d}") for i in range(200))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "partial.json"
            arguments = ["search_arxiv_html.py", "--since", "2023-01-01", "--until", "2023-12-31",
                         "--max-pages", "1", "--cache-dir", directory, "--output", str(destination)]
            with patch.object(module, "CACHE", Path(directory)), patch.object(module, "fetch", return_value=raw), \
                    patch.object(sys, "argv", arguments), contextlib.redirect_stdout(io.StringIO()):
                result = module.main()
            data = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(result, 1)
        self.assertEqual(data["source_status"]["arxiv"]["status"], "failed")
        self.assertEqual(len(data["records"]), 200)
        self.assertIn("Pagination limit", data["source_status"]["arxiv"]["errors"][0])


if __name__ == "__main__":
    unittest.main()
