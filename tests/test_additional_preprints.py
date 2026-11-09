import json
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import search_additional_preprints as module
import search_preprints as sp
import journal_policy as jp


class AdditionalPreprintTests(unittest.TestCase):
    def test_text_ending_with_ampersand_word_is_retained(self):
        title = "SPACE-Tag Enables High-Throughput Spatial Chromatin Profiling With CUT&Tag"
        self.assertEqual("".join(module.AbstractText(title).parts), title)
        row = {"id": "PPR1", "source": "PPR", "title": title,
               "abstractText": "<p>Spatial chromatin profiling</p> with CUT&Tag"}
        record = module.parse_record(row, "https://example.org/query")
        self.assertEqual(record["abstract"], "Spatial chromatin profiling with CUT&Tag")

    def test_null_abstract_keeps_the_candidate(self):
        row = {"id": "PPR1", "source": "PPR", "title": "Histopathology benchmark",
               "abstractText": None, "doi": None}
        record = module.parse_record(row, "https://example.org/query")
        self.assertEqual(record["abstract"], "")
        self.assertEqual(record["title"], row["title"])

    def test_linked_formal_dois_participate_in_matching_and_exclusion(self):
        doi = "10.1038/s41598-025-19195-0"
        row = {"id": "PPR1", "source": "PPR", "title": "A retitled preprint",
               "commentCorrectionList": {"commentCorrection": [
                   {"type": "Preprint of", "doi": doi},
                   {"type": "Preprint of", "source": "MED", "id": "123"},
                   {"type": "Erratum in", "doi": "10.1234/unrelated"}]}}
        record = module.parse_record(row, "https://example.org/query")
        self.assertEqual(record["linked_publication_dois"], [doi])
        self.assertTrue(record["publication_identity_pending"])
        self.assertIn("https://europepmc.org/article/MED/123", record["linked_publication_urls"])
        exclusions = {"title_sha256": [], "identifiers": ["doi:" + doi]}
        self.assertIsNotNone(sp.journal_policy_exclusion(record, exclusions))
        entry = {"key": sp.normalized("Formal title"), "paper_url": "https://doi.org/" + doi}
        self.assertEqual(sp.matching_existing(record, [entry]), [entry])

    def test_invalid_cached_index_pages_are_refetched(self):
        import hashlib
        url = "https://example.org/index"
        valid = {"hitCount": 0, "resultList": {"result": []}}
        raw = json.dumps(valid).encode()
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            destination = cache / (hashlib.sha256(url.encode()).hexdigest() + ".response")
            for invalid in [b"{bad", b'{"hitCount":1}', b'{"hitCount":1,"resultList":null}']:
                with self.subTest(invalid=invalid):
                    destination.write_bytes(invalid)
                    with patch.object(sp.urllib.request, "urlopen") as request, patch.object(sp.time, "sleep"):
                        request.return_value.__enter__.return_value.read.return_value = raw
                        result = sp.request(url, cache, "test", validator=module.validate_index_page)
                        self.assertEqual(json.loads(result), valid)
                        request.assert_called_once()
                    self.assertEqual(destination.read_bytes(), raw)
            with patch.object(sp.urllib.request, "urlopen") as request, patch.object(sp.time, "sleep"):
                request.return_value.__enter__.return_value.read.return_value = raw
                sp.request(url, cache, "test", validator=module.validate_index_page, refresh=True)
                request.assert_called_once()

    def test_saved_discovery_frontier_does_not_advance_review_checkpoint(self):
        source = {"last_successful_until": None, "last_retrieval_until": "2026-11-07",
                  "retrieval_status": "complete_for_recorded_yearly_index_queries", "pending_files": ["queue.json"]}
        state = {"additional_sources": {"europepmc_preprints": source}}
        config = {"lookback_overlap_days": 14}
        self.assertEqual(module.default_since(state, config, "updated"), "2026-10-24")
        self.assertIsNone(source["last_successful_until"])
        self.assertEqual(module.default_since(state, config, "first"), "2023-01-01")
        source["retrieval_status"] = "failed"
        self.assertEqual(module.default_since(state, config, "updated"), "2023-01-01")

    def test_default_outputs_preserve_separate_intervals_and_rescans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "data").mkdir()
            (root / "config/literature-keywords.json").write_text(json.dumps({"lookback_overlap_days": 14}))
            (root / "data/weekly-update-state.json").write_text("{}")
            (root / "data/excluded-journal-identities.json").write_text("{}")
            with patch.object(module, "ROOT", root), patch.object(module, "collect"), \
                    patch.object(sp, "existing_entries", return_value=[]), contextlib.redirect_stdout(io.StringIO()):
                for year in [2023, 2024, 2023]:
                    with patch.object(sys, "argv", ["search", "--since", f"{year}-01-01", "--until", f"{year}-12-31"]):
                        self.assertEqual(module.main(), 0)
            packets = list(root.rglob("candidates-*.json"))
            self.assertEqual(len(packets), 3)
            self.assertEqual(len({packet.parent for packet in packets}), 3)
            self.assertTrue(any("2024-01-01" in packet.name for packet in packets))

    def test_discovery_platforms_have_preprint_venue_types(self):
        policy = json.loads((ROOT / "config/journal-policy.json").read_text(encoding="utf-8"))
        for venue in set(module.PLATFORMS.values()):
            self.assertEqual(jp.venue_type(venue, policy), "preprint", venue)

    def test_bad_candidate_preserves_raw_records_and_other_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "data").mkdir()
            config = {"lookback_overlap_days": 14, "topic_groups": {"histology": ["histopathology"]},
                      "method_terms": [], "biological_context_terms": ["histopathology"]}
            (root / "config/literature-keywords.json").write_text(json.dumps(config))
            (root / "data/weekly-update-state.json").write_text("{}")
            (root / "data/excluded-journal-identities.json").write_text(json.dumps({"identifiers": [], "title_sha256": []}))

            def collect(config, since, until, field, cache, log, records, cap, refresh):
                records[("PPR", "1")] = {"id": "1", "source": "PPR", "title": "Histopathology model"}
                records[("PPR", "2")] = {"id": "2", "source": "PPR", "title": None}

            destination = root / "candidates.json"
            with patch.object(module, "ROOT", root), patch.object(module, "collect", side_effect=collect), \
                    patch.object(sp, "existing_entries", return_value=[]), contextlib.redirect_stdout(io.StringIO()), \
                    patch.object(sys, "argv", ["search", "--since", "2023-01-01", "--until", "2023-12-31", "--output", str(destination)]):
                self.assertEqual(module.main(), 1)
            payload = json.loads(destination.read_text())
            self.assertEqual(len(payload["records"]), 2)
            self.assertEqual(len(payload["candidates"]), 1)
            self.assertEqual(payload["source_status"]["europepmc_preprints"]["status"], "failed")
            self.assertIn("PPR:2", payload["source_status"]["europepmc_preprints"]["errors"][0])

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
        self.assertFalse(result["accepted_without_formal_link"])
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
        self.assertEqual(record["abstract"], "P < 0.05, followed by tissue analysis. Final histopathology result.")

    def test_research_square_sentinel_and_version_identity(self):
        expected = ("doi", "10.21203/rs.3.rs-9949149")
        for value in ["10.21203/rs.3.rs-9949149/v1", "https://doi.org/10.21203/rs.3.rs-9949149/v2",
                      "https://www.researchsquare.com/article/rs-9949149/v1"]:
            self.assertEqual(sp.paper_identity(value), expected)
        self.assertEqual(module.platform_for(expected[1]), "Research Square")
        config = json.loads((ROOT / "config/literature-keywords.json").read_text(encoding="utf-8"))
        record = {"title": "Genome-scale molecular profiling from routine histopathology with a multimodal pathology foundation model"}
        self.assertTrue(sp.topic_matches(record, config)[0])
        self.assertTrue(any("TITLE_ABS:pathology" in query for _, _, query in module.queries(config, "2023-01-01", "2026-11-07", "first")))

    def test_preprints_org_revisions_and_legacy_exclusions(self):
        for value in ["10.14293/PR2199.003544.v1", "10.14293/PR2199.003544.v2"]:
            self.assertEqual(sp.paper_identity(value), ("doi", "10.14293/pr2199.003544"))
        for value in ["https://www.preprints.org/manuscript/202610.2346/v2", "10.20944/preprints202610.2346.v1"]:
            self.assertEqual(sp.paper_identity(value), ("doi", "10.20944/preprints202610.2346"))
        record = {"title": "Retitled paper", "id": "10.21203/rs.3.rs-123/v3"}
        exclusions = {"title_sha256": [], "identifiers": ["doi:10.21203/rs.3.rs-123/v1"]}
        self.assertIsNotNone(sp.journal_policy_exclusion(record, exclusions))
        self.assertIsNone(sp.journal_policy_exclusion({**record, "id": "10.21203/rs.3.rs-456/v1"}, exclusions))

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
        row["title"] = "An active atlas"
        self.assertFalse(module.parse_record(row, "https://example.org/query")["withdrawn_or_removed"])
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
