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
    def test_publisher_doi_identity_survives_preprint_title_changes(self):
        for url, doi in [
            ("https://www.nature.com/articles/s41591-024-02857-3.pdf?download=1",
             "10.1038/s41591-024-02857-3"),
            ("https://link.springer.com/article/10.1007/s10115-024-00123-4",
             "10.1007/s10115-024-00123-4"),
        ]:
            self.assertEqual(module.paper_identity(url), ("doi", doi))
            existing = [{"title": "Retitled formal article", "key": "retitledformalarticle",
                         "paper_url": url, "identity_urls": [url]}]
            record = {"title": "Original preprint title", "id": "2308.12345", "doi": doi}
            self.assertEqual(module.matching_existing(record, existing), existing)
        self.assertIsNone(module.paper_identity("https://www.nature.com/collections/example"))
        self.assertIsNone(module.paper_identity("https://www.nature.com/articles/palcomms20155"))

    def test_plain_pathology_workflow_reaches_search_and_screening(self):
        config = json.loads((ROOT / "config/literature-keywords.json").read_text())
        record = {
            "title": "PathCowork: Learning from real-world pathology practice to build AI copilots",
            "abstract": "Doctors' spoken examinations and gaze provide supervision for diagnostic agents.",
        }
        self.assertTrue(module.topic_matches(record, config)[0])
        queries = list(module.arxiv_queries(config))
        self.assertTrue(any("ti:pathology OR abs:pathology" in q for _, _, q in queries))
        self.assertGreater(len(queries), len(config["topic_groups"]))
        self.assertTrue(all(q.count("ti:") <= 12 for _, _, q in queries))

    def test_cell_tissue_analysis_does_not_require_a_method_buzzword(self):
        config = json.loads((ROOT / "config/literature-keywords.json").read_text())
        record = {"title": "Single-nucleus states in the kidney", "abstract": "Renal populations differ."}
        self.assertTrue(module.topic_matches(record, config)[0])

    def test_promoted_paper_with_changed_title_matches_retained_preprint_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "papers").mkdir()
            (root / "README.md").write_text("# Papers\n", encoding="utf-8")
            (root / "papers/2026.md").write_text(
                "## NeurIPS 2026\n\n"
                "- PathNavigate: Whole-Slide VQA [[paper](https://neurips.cc/virtual/2026/poster/154224)]"
                "[[preprint](https://arxiv.org/abs/2605.23559v1)]\n"
                "- An unrelated WSI model [[paper](https://arxiv.org/abs/2605.23558)]\n", encoding="utf-8")
            with patch.object(module, "ROOT", root):
                previous = module.existing_entries()
        record = {"id": "2605.23559v3", "title": "PathNavigate: Whole-Slide Image VQA"}
        self.assertNotEqual(previous[0]["key"], module.normalized(record["title"]))
        self.assertEqual(module.matching_existing(record, previous), [previous[0]])

    def test_identity_prefix_does_not_match_an_unrelated_paper(self):
        url = "https://www.biorxiv.org/content/10.1101/example2v3.full.pdf?download=1"
        previous = [{"title": "Different paper", "key": module.normalized("Different paper"),
                     "paper_url": url, "identity_urls": [url]}]
        self.assertEqual(module.matching_existing({"id": "10.1101/example", "title": "New paper"}, previous), [])
        self.assertEqual(module.matching_existing({"id": "10.1101/example2", "title": "Changed title"}, previous), previous)
        previous[0]["paper_url"] = "https://arxiv.org/abs/1405.12345v2"
        previous[0]["identity_urls"] = [previous[0]["paper_url"]]
        self.assertEqual(module.matching_existing({"id": "1405.1234", "title": "New paper"}, previous), [])

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
            result = module.rxiv_records("biorxiv", "2026-10-01", "2026-10-04", Path("unused"), log,
                                         category="pathology")
        self.assertEqual(mock.call_count, 2)
        self.assertIn("/2/json", mock.call_args.args[0])
        self.assertTrue(all("?category=pathology" in call.args[0]
                            for call in mock.call_args_list))
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
