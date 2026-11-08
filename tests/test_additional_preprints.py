import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import search_additional_preprints as module
import search_preprints as sp


class AdditionalPreprintTests(unittest.TestCase):
    def test_ssrn_original_urls_share_doi_identity(self):
        expected = ("doi", "10.2139/ssrn.6506743")
        for url in ["https://ssrn.com/abstract=6506743",
                    "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6506743",
                    "https://papers.ssrn.com/sol3/Delivery.cfm/paper.pdf?abstractid=6506743&type=2"]:
            self.assertEqual(sp.paper_identity(url), expected)
        self.assertIsNone(sp.paper_identity("https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=6506743"))

    def test_explicit_html_status_fetch_does_not_weaken_api_cache_validation(self):
        import hashlib
        url = "https://example.org/status"
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / (hashlib.sha256(url.encode()).hexdigest() + ".response")).write_bytes(b"<html>article</html>")
            with self.assertRaises(ValueError):
                sp.request(url, cache, "api")
            self.assertEqual(sp.request(url, cache, "status", allow_html=True), b"<html>article</html>")

    def test_submission_journal_does_not_establish_formal_publication(self):
        data = {"doi": "10.21203/rs.3.rs-9949149/v1", "manuscriptTitle": "Fuji",
                "journal": {"title": "Nature Portfolio"}, "isAcceptedByJournal": False,
                "nonDraftVersions": [{"code": 1, "date": "2026-08-06 04:49:17"}]}
        payload = {"props": {"pageProps": {"initialData": data}}}
        raw = ('<script id="__NEXT_DATA__" type="application/json">' + json.dumps(payload) + '</script>').encode()
        with patch.object(sp, "request", return_value=raw):
            result = module.research_square_details(data["doi"], Path("unused"))
        self.assertIsNone(result["formal_doi"])
        self.assertEqual(result["status"], "preprint_no_formal_link")
        self.assertEqual(result["first_posted"], "2026-08-06")
        data["isAcceptedByJournal"] = True
        payload["props"]["pageProps"]["initialData"] = data
        raw = ('<script id="__NEXT_DATA__">' + json.dumps(payload) + '</script>').encode()
        with patch.object(sp, "request", return_value=raw):
            result = module.research_square_details(data["doi"], Path("unused"))
        self.assertTrue(result["accepted_without_formal_link"])

    def test_abstract_markup_and_comparisons_preserve_remaining_text(self):
        row = {"id": "PPR1", "source": "PPR", "title": "A model",
               "abstractText": "<p>P<0.05, followed by tissue analysis.</p><p>Final <b>histopathology</b> result.</p>"}
        record = module.parse_record(row, "https://example.org/query")
        self.assertIn("0.05", record["abstract"])
        self.assertIn("Final", record["abstract"])
        self.assertIn("histopathology", record["abstract"])

    def test_research_square_sentinel_and_version_identity(self):
        expected = ("doi", "10.21203/rs.3.rs-9949149")
        for value in ["10.21203/rs.3.rs-9949149/v1", "https://doi.org/10.21203/rs.3.rs-9949149/v2",
                      "https://www.researchsquare.com/article/rs-9949149/v1"]:
            self.assertEqual(sp.paper_identity(value), expected)
        self.assertEqual(module.platform_for(expected[1]), "Research Square")
        config = json.loads((ROOT / "config/literature-keywords.json").read_text())
        record = {"title": "Genome-scale molecular profiling from routine histopathology with a multimodal pathology foundation model"}
        self.assertTrue(sp.topic_matches(record, config)[0])
        self.assertTrue(any("TITLE_ABS:pathology" in query for _, _, query in module.queries(config, "2023-01-01", "2026-11-07", "first")))

    def test_preprints_org_revisions_and_legacy_exclusions(self):
        self.assertEqual(sp.paper_identity("10.14293/PR2199.003544.v1"),
                         sp.paper_identity("10.14293/PR2199.003544.v2"))
        self.assertEqual(sp.paper_identity("https://www.preprints.org/manuscript/202610.2346/v2"),
                         sp.paper_identity("10.20944/preprints202610.2346.v1"))
        record = {"title": "Retitled paper", "id": "10.21203/rs.3.rs-123/v3"}
        exclusions = {"title_sha256": [], "identifiers": ["doi:10.21203/rs.3.rs-123/v1"]}
        self.assertIsNotNone(sp.journal_policy_exclusion(record, exclusions))

    def test_first_version_date_and_withdrawal_are_explicit(self):
        row = {"id": "PPR1", "source": "PPR", "doi": "10.21203/rs.3.rs-123/v2",
               "title": "An atlas", "firstPublicationDate": "2026-10-01", "versionNumber": 2,
               "pubTypeList": {"pubType": ["preprint-withdrawal"]},
               "versionList": {"version": [{"versionNumber": 1, "firstPublishDate": "2022-05-01"}]}}
        record = module.parse_record(row, "https://example.org/query")
        self.assertEqual(record["first_posted_provisional"], "2022-05-01")
        self.assertTrue(record["withdrawn_or_removed"])
        row["title"] = "WITHDRAWN: An atlas"
        row["pubTypeList"] = {"pubType": ["Preprint"]}
        self.assertTrue(module.parse_record(row, "https://example.org/query")["withdrawn_or_removed"])
        self.assertIsNone(module.platform_for("10.99999/unknown"))

    def test_incomplete_cursor_raises_and_preserves_partial_records(self):
        config = {"topic_groups": {"histology": ["histology"]}}
        page = {"hitCount": 2, "resultList": {"result": [{"id": "PPR1", "source": "PPR"}]},
                "nextCursorMark": "*"}
        records, log = {}, []
        with patch.object(sp, "request", return_value=json.dumps(page).encode()):
            with self.assertRaises(ValueError):
                module.collect(config, "2023-01-01", "2023-12-31", "first", Path("unused"), log, records)
        self.assertIn(("PPR", "PPR1"), records)
        self.assertEqual(log[0]["retrieved"], 1)


if __name__ == "__main__":
    unittest.main()
