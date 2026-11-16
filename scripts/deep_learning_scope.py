"""Validate recorded deep-learning admission evidence for the active bibliography."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

from journal_policy import collection_entries
from search_preprints import matches_exclusion_identities, normalized, paper_identity

ROOT = Path(__file__).resolve().parents[1]
RELATIONS = {"research", "supporting_resource"}


def title_hash(title):
    return hashlib.sha256(normalized(title).encode()).hexdigest()


def validate_scope(root=ROOT):
    evidence = {}
    for path in sorted((root / "data/deep-learning-evidence").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload["entries"]:
            key = entry["title_sha256"]
            if key != title_hash(entry["title"]):
                raise ValueError(f"Evidence title/hash mismatch in {path}")
            if (entry["relation"] not in RELATIONS or not entry["scope_rationale"].strip()
                    or not entry["source_url"].startswith(("https://", "http://"))):
                raise ValueError(f"Incomplete deep-learning evidence in {path}: {entry['title']}")
            if key in evidence:
                raise ValueError(f"Repeated evidence title in {path}: {entry['title']}")
            evidence[key] = entry
    exclusions = json.loads((root / "data/excluded-method-identities.json").read_text(encoding="utf-8"))
    seen = set()
    errors = []
    active_count = 0
    for path, number, year, venue, line in collection_entries(root):
        active_count += 1
        title = line[2:].split("[[paper]", 1)[0].strip()
        key = title_hash(title)
        urls = [unquote(url) for url in re.findall(
            r"\[\[(?:paper|preprint|arxiv|biorxiv|medrxiv)\]\((.*?)\)\]", line, re.I)]
        if not urls:
            errors.append(f"{path.relative_to(root)}:{number}: missing publication link")
            continue
        record = {"title": title, "id": urls[0], "linked_publication_dois": urls[1:]}
        if matches_exclusion_identities(record, exclusions):
            errors.append(f"{path.relative_to(root)}:{number}: prior scope removal/pending identity")
        entry = evidence.get(key)
        if entry is None:
            errors.append(f"{path.relative_to(root)}:{number}: missing deep-learning admission evidence")
            continue
        known_urls = set(entry["paper_urls"])
        known_ids = {paper_identity(url) for url in known_urls}
        known_ids.discard(None)
        if not any(url in known_urls or paper_identity(url) in known_ids for url in urls):
            errors.append(f"{path.relative_to(root)}:{number}: evidence publication identity mismatch")
        seen.add(key)
    for key in evidence.keys() - seen:
        errors.append(f"Orphaned deep-learning evidence: {evidence[key]['title']}")
    if errors:
        raise ValueError("Deep-learning scope validation failed\n" + "\n".join(errors))
    return {"active_entries": active_count, "evidence_records": len(seen)}


if __name__ == "__main__":
    print(json.dumps(validate_scope(), ensure_ascii=False))
