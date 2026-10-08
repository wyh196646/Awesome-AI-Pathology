"""Reject journal entries without verified CAS major-zone-1 and SCIE evidence."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def venue_key(name):
    return re.sub(r"[^a-z0-9]", "", html.unescape(name).lower().replace("&", "and"))


def venue_type(name, policy):
    if name in policy["preprint_servers"]:
        return "preprint"
    if name in policy["technical_reports"]:
        return "technical_report"
    match = re.fullmatch(r"(.+?) 20\d{2}(?: Workshops?)?", name)
    if match and match[1] in policy["conferences"]:
        return "conference"
    key = venue_key(name)
    for journal in policy["journals"]:
        if key in {venue_key(n) for n in [journal["title"], *journal["aliases"]]}:
            if (journal["cas_major_zone"] == policy["required_zone"] == 1 and
                    "SCIE" in journal["wos_index"].split(", ") and
                    journal.get("cas_source") in policy["sources"] and
                    journal.get("current_index_source") in policy["sources"]):
                return "journal"
            break
    return "ineligible_or_unverified_journal"


def collection_entries(root=ROOT):
    for path in [root / "README.md", *sorted((root / "papers").glob("*.md"))]:
        year = int(path.stem) if path.stem.isdigit() else None
        venue = None
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = re.fullmatch(r"# (\d{4})", line)
            if match:
                year, venue = int(match[1]), None
            if line.startswith("## "):
                venue = line[3:]
            if path.name == "README.md" and year is not None and year < 2023:
                match = re.fullmatch(r"\*\*(.+?)\*\*", line)
                if match:
                    venue = match[1]
            if line.startswith("- ") and "[[paper]" in line:
                if year is None or venue is None:
                    raise ValueError(f"Paper without year/venue: {path}:{number}")
                yield path, number, year, venue, line


def validate_collection(root=ROOT):
    policy = json.loads((root / "config/journal-policy.json").read_text(encoding="utf-8"))
    if policy["partition"] != "major" or policy["required_index"] != "SCIE":
        raise ValueError("Journal policy must use CAS major partitions and SCIE membership")
    counts = {"journal": 0, "conference": 0, "preprint": 0, "technical_report": 0}
    errors = []
    for path, number, year, venue, line in collection_entries(root):
        kind = venue_type(venue, policy)
        if kind not in counts:
            errors.append(f"{path.relative_to(root)}:{number}: {venue}")
        else:
            counts[kind] += 1
    if errors:
        raise ValueError("Journal entries outside the verified CAS zone-1 allowlist:\n" + "\n".join(errors))
    return counts


if __name__ == "__main__":
    print(json.dumps(validate_collection(), ensure_ascii=False))
