"""Regression checks for scope evidence and cross-version review flags."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deep_learning_scope as scope
import search_preprints as search


class DeepLearningScopeTests(unittest.TestCase):
    def make_collection(self, root):
        (root / "papers").mkdir()
        (root / "data/deep-learning-evidence").mkdir(parents=True)
        title = "A neural histology model"
        url = "https://arxiv.org/abs/2610.12345v2"
        (root / "README.md").write_text(
            f"# 2026\n\n## arXiv\n\n- {title} [[paper]({url})]\n", encoding="utf-8")
        evidence = {"entries": [{
            "title": title, "title_sha256": scope.title_hash(title),
            "paper_urls": [url], "relation": "research",
            "scope_rationale": "Trains a convolutional pathology classifier.",
            "source_url": url,
        }]}
        (root / "data/deep-learning-evidence/2026.json").write_text(json.dumps(evidence))
        registry = {"identifiers": [], "title_sha256": []}
        (root / "data/excluded-method-identities.json").write_text(json.dumps(registry))
        return evidence, registry

    def test_active_collection_has_complete_evidence(self):
        self.assertEqual(scope.validate_scope(ROOT)["active_entries"],
                         len(search.existing_entries()))

    def test_valid_evidence_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence, registry = self.make_collection(root)
            self.assertEqual(scope.validate_scope(root)["active_entries"], 1)
            (root / "data/deep-learning-evidence/2026.json").write_text('{"entries": []}')
            with self.assertRaisesRegex(ValueError, "missing deep-learning admission evidence"):
                scope.validate_scope(root)

    def test_pending_identity_cannot_silently_return(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence, registry = self.make_collection(root)
            registry["identifiers"] = ["arxiv:2610.12345"]
            (root / "data/excluded-method-identities.json").write_text(json.dumps(registry))
            with self.assertRaisesRegex(ValueError, "prior scope removal/pending identity"):
                scope.validate_scope(root)

    def test_different_publication_requires_evidence_identity_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence, registry = self.make_collection(root)
            evidence["entries"][0]["paper_urls"] = ["https://doi.org/10.1234/different"]
            (root / "data/deep-learning-evidence/2026.json").write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError, "publication identity mismatch"):
                scope.validate_scope(root)

    def test_scope_flag_uses_linked_doi_across_renamed_versions(self):
        registry = {"title_sha256": [], "identifiers": ["doi:10.1234/known"]}
        record = {"id": "2610.99999v3", "title": "A changed title",
                  "linked_publication_dois": ["10.1234/known"]}
        self.assertIsNotNone(search.method_scope_exclusion(record, registry))
        record["linked_publication_dois"] = []
        self.assertIsNone(search.method_scope_exclusion(record, registry))


if __name__ == "__main__":
    unittest.main()
