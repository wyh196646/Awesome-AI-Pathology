"""Protect the journal threshold across old entries and future weekly promotions."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("policy", ROOT / "scripts/journal_policy.py")
policy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy_module)
spec = importlib.util.spec_from_file_location("collector", ROOT / "scripts/search_preprints.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class JournalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/journal-policy.json").read_text(encoding="utf-8"))

    def test_scie_zone_1_journals_are_kept_and_jcr_q1_is_insufficient(self):
        for venue in ["Medical Image Analysis", "IEEE Transactions on Medical Imaging",
                      "IEEE Transactions on Pattern Analysis and Machine Intelligence"]:
            self.assertEqual(policy_module.venue_type(venue, self.policy), "journal")
        for venue in ["Bioinformatics", "Briefings in Bioinformatics", "Scientific Reports",
                      "IEEE Journal of Biomedical and Health Informatics", "Cell Genomics",
                      "MedComm", "npj Imaging", "Nature 2026"]:
            self.assertEqual(policy_module.venue_type(venue, self.policy), "ineligible_or_unverified_journal")

    def test_conferences_preprints_and_verified_title_aliases(self):
        for venue, kind in [("MICCAI 2026", "conference"), ("NeurIPS 2026 Workshops", "conference"),
                            ("PSB 2024", "conference"), ("arXiv", "preprint"),
                            ("Harvard Thesis", "technical_report"),
                            ("The American Journal of Surgical Pathology", "journal")]:
            self.assertEqual(policy_module.venue_type(venue, self.policy), kind)

    def test_validation_checks_inline_old_years_and_annual_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "papers").mkdir()
            (root / "config/journal-policy.json").write_text(json.dumps(self.policy), encoding="utf-8")
            (root / "README.md").write_text(
                "# 2017\n\n**Scientific Reports**\n\n- Old paper [[paper](https://doi.org/10.1/old)]\n",
                encoding="utf-8")
            (root / "papers/2026.md").write_text(
                "# Papers in 2026\n\n## Medical Image Analysis\n\n- New paper [[paper](https://doi.org/10.1/new)]\n",
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "README.md:5: Scientific Reports"):
                policy_module.validate_collection(root)
            (root / "README.md").write_text("# Papers\n", encoding="utf-8")
            self.assertEqual(policy_module.validate_collection(root)["journal"], 1)

    def test_removed_formal_publication_is_flagged_by_title_or_complete_identifier(self):
        exclusions = {"title_sha256": {hashlib.sha256(collector.normalized("Tissue atlas").encode()).hexdigest()},
                      "identifiers": {"doi:10.1234/excluded", "arxiv:2401.12345"}}
        for record in [{"id": "10.1101/new", "title": "Tissue atlas"},
                       {"id": "10.1101/new", "title": "Changed title", "published_doi": "10.1234/excluded"},
                       {"id": "2401.12345v3", "title": "Changed title"}]:
            self.assertIsNotNone(collector.journal_policy_exclusion(record, exclusions))
        self.assertIsNone(collector.journal_policy_exclusion(
            {"id": "10.1234/excluded-other", "title": "Unpublished study"}, exclusions))


if __name__ == "__main__":
    unittest.main()
