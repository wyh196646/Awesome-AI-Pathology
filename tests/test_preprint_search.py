"""Guard against silent omissions, duplicate revisions and lexical false positives."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("preprints", ROOT / "scripts/search_preprints.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreprintSearchTests(unittest.TestCase):
    def test_promoted_paper_with_changed_title_matches_retained_preprint_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "papers").mkdir()
            (root / "README.md").write_text("# Papers\n", encoding="utf-8")
            (root / "papers/2026.md").write_text(
                "## NeurIPS 2026\n\n"
                "- PathNavigate: Whole-Slide VQA [[paper](https://neurips.cc/virtual/2026/poster/154224)]"
                "[[preprint](https://arxiv.org/abs/2605.23559)]\n", encoding="utf-8")
            with patch.object(module, "ROOT", root):
                previous = module.existing_entries()
        record = {"id": "2605.23559", "title": "PathNavigate: Whole-Slide Image VQA"}
        self.assertNotEqual(previous[0]["key"], module.normalized(record["title"]))
        self.assertEqual(len(module.matching_existing(record, previous)), 1)

    def test_histology_and_spatial_methods_do_not_need_pathology_in_title(self):
        config = json.loads((ROOT / "config/literature-keywords.json").read_text())
        for record in [
            {"title": "Improving Representation Learning with Cluster Constraints",
             "abstract": "We learn representations from histopathologic tissue images."},
            {"title": "Spatial transcriptomics domain clustering with graphs", "abstract": "No images are required."},
            {"title": "Cross-modal cell annotation", "abstract": "Integration of single-cell RNA and ATAC data."},
        ]:
            self.assertTrue(module.topic_matches(record, config)[0])

    def test_generic_spatial_and_single_cell_meanings_are_not_candidates(self):
        config = json.loads((ROOT / "config/literature-keywords.json").read_text())
        for record in [
            {"title": "Spatial alignment for astronomical images", "abstract": "A neural network model."},
            {"title": "Search for a single cell architecture", "abstract": "Neural architecture search."},
            {"title": "The h and e expansions", "abstract": "A combinatorial algorithm for polynomials."},
        ]:
            self.assertFalse(module.topic_matches(record, config)[0])

    def test_rxiv_paginates_and_keeps_latest_revision(self):
        def item(version, doi="10.64898/example"):
            return {"doi": doi, "title": "A tissue atlas", "date": "2026-10-01", "version": version}
        responses = [
            {"messages": [{"status": "ok", "total": "3"}], "collection": [item(1), item(2)]},
            {"messages": [{"status": "ok", "total": "3"}], "collection": [item(1, "10.1101/other")]},
        ]
        log = []
        with patch.object(module, "request", side_effect=[json.dumps(x).encode() for x in responses]) as mock:
            result = module.rxiv_records("biorxiv", "2026-10-01", "2026-10-04", Path("unused"), log)
        self.assertEqual(mock.call_count, 2)
        self.assertIn("/2/json", mock.call_args.args[0])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["version"], 2)

    def test_rxiv_refuses_incomplete_page_and_api_error(self):
        for response in [
            {"messages": [{"status": "ok", "total": "5"}], "collection": []},
            {"messages": [{"status": "error"}], "collection": []},
            {"messages": [{"status": "ok"}], "collection": []},
        ]:
            with patch.object(module, "request", return_value=json.dumps(response).encode()):
                with self.assertRaises(ValueError):
                    module.rxiv_records("medrxiv", "2026-10-01", "2026-10-04", Path("unused"), [])

    def test_rxiv_refuses_out_of_window_date(self):
        response = {"messages": [{"status": "ok", "total": 1}], "collection": [
            {"doi": "10.1101/example", "title": "Atlas", "date": "2026-09-01", "version": 1}]}
        with patch.object(module, "request", return_value=json.dumps(response).encode()):
            with self.assertRaises(ValueError):
                module.rxiv_records("biorxiv", "2026-10-01", "2026-10-04", Path("unused"), [])

    def test_arxiv_revised_old_paper_retains_first_posted_year(self):
        feed = b'''<feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:o="http://a9.com/-/spec/opensearch/1.1/">
          <o:totalResults>1</o:totalResults><entry><id>http://arxiv.org/abs/2301.01234v3</id>
          <title>Spatial transcriptomics model</title><summary>Graph learning.</summary>
          <published>2023-01-03T00:00:00Z</published><updated>2026-10-01T00:00:00Z</updated>
          </entry></feed>'''
        config = {"topic_groups": {"spatial": ["spatial transcriptomics"]}, "arxiv_page_size": 2,
                  "arxiv_max_pages_per_group": 2}
        with patch.object(module, "request", return_value=feed):
            result = module.arxiv_records(config, "2026-09-21", "2026-10-04", Path("unused"), [])
        self.assertEqual(result[0]["year"], 2023)
        self.assertEqual(result[0]["id"], "2301.01234")
        self.assertEqual(result[0]["version"], 3)

    def test_arxiv_pagination_cap_is_failure(self):
        feed = b'''<feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>100</o:totalResults>
          <entry><id>http://arxiv.org/abs/2610.01234v1</id><title>Atlas</title>
          <published>2026-10-01T00:00:00Z</published><updated>2026-10-01T00:00:00Z</updated></entry></feed>'''
        config = {"topic_groups": {"spatial": ["atlas"]}, "arxiv_page_size": 1,
                  "arxiv_max_pages_per_group": 1}
        with patch.object(module, "request", return_value=feed):
            with self.assertRaises(RuntimeError):
                module.arxiv_records(config, "2026-09-21", "2026-10-04", Path("unused"), [])


if __name__ == "__main__":
    unittest.main()
