"""Discover additional preprint platforms through Europe PMC's public index.

Python 3.10+, standard library only. Original server status, formal publication,
first-version dates and topical admission require separate review. This collector
never edits the bibliography or advances checkpoints.
"""
import argparse
import datetime as dt
import html
import hashlib
import json
import re
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

import search_preprints as sp

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PLATFORMS = {
    "10.21203/": "Research Square",
    "10.20944/preprints": "Preprints.org",
    "10.2139/ssrn.": "SSRN",
    "10.31219/": "OSF Preprints",
    "10.31234/": "OSF Preprints",
    "10.31222/": "OSF Preprints",
    "10.22541/": "Authorea",
    "10.36227/": "TechRxiv",
    "10.5281/zenodo.": "Zenodo",
    "10.1590/scielopreprints.": "SciELO Preprints",
    "10.14293/pr": "ScienceOpen Preprints",
}


class AbstractText(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.parts = []
        self.feed(value)

    def handle_data(self, value):
        self.parts.append(value)


def platform_for(doi):
    return next((name for prefix, name in PLATFORMS.items() if doi.lower().startswith(prefix)), None)


def research_square_details(doi, cache):
    match = re.fullmatch(r"10\.21203/rs\.3\.rs-(\d+)(?:/v(\d+))?", doi.lower())
    if not match:
        raise ValueError("A Research Square article DOI is required")
    url = f"https://www.researchsquare.com/article/rs-{match[1]}/v{match[2] or '1'}"
    raw = sp.request(url, cache, "researchsquare", allow_html=True).decode("utf-8")
    script = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', raw, re.S)
    if not script:
        raise ValueError("Research Square page lacks primary article metadata")
    data = json.loads(script[1])["props"]["pageProps"]["initialData"]
    if sp.paper_identity(data["doi"]) != sp.paper_identity(doi):
        raise ValueError("Research Square article identity mismatch")
    dates = [version["date"][:10] for version in data.get("nonDraftVersions", [])
             if str(version.get("code")) == "1" and version.get("date")]
    formal = data.get("vorDoi") or None
    accepted = bool(data.get("isAcceptedByJournal"))
    status = "preprint_no_formal_link"
    if formal:
        status = "published_version_linked"
    elif accepted:
        status = "publication_identity_pending"
    journal = data.get("journal")
    return {
        "doi": data["doi"], "source_url": url,
        "title": html.unescape(data.get("manuscriptTitle", "")),
        "first_posted": min(dates) if dates else None,
        "formal_doi": formal,
        "accepted_without_formal_link": accepted and not formal,
        "status": status,
        "submission_journal": journal.get("title") if isinstance(journal, dict) else None,
    }


def queries(config, since, until, date_field):
    field = {"first": "FIRST_PDATE", "updated": "UPDATE_DATE"}[date_field]
    base = (f"(SRC:PPR OR PUB_TYPE:preprint) AND {field}:[{since} TO {until}] "
            "AND NOT (DOI:10.1101* OR DOI:10.64898* OR DOI:10.48550*)")
    for group, terms in config["topic_groups"].items():
        for start in range(0, len(terms), 32):
            clauses = ["TITLE_ABS:" + ('"' + term.replace('"', '') + '"' if " " in term else term)
                       for term in terms[start:start + 32]]
            yield group, start // 32, base + " AND (" + " OR ".join(clauses) + ")"


def parse_record(row, url):
    doi = row.get("doi", "").lower()
    types = [value.lower() for value in row.get("pubTypeList", {}).get("pubType", [])]
    versions = row.get("versionList", {}).get("version", [])
    first = [version["firstPublishDate"] for version in versions
             if version.get("versionNumber") == 1 and version.get("firstPublishDate")]
    return {
        "source": "europepmc", "id": doi or row["source"] + ":" + row["id"],
        "doi": doi, "index_id": row["id"], "index_source": row["source"],
        "platform": platform_for(doi),
        "publisher": row.get("bookOrReportDetails", {}).get("publisher", ""),
        "title": html.unescape(row["title"]),
        "abstract": " ".join(AbstractText(row.get("abstractText", "")).parts),
        "authors": row.get("authorString", ""),
        "author_details": row.get("authorList", {}).get("author", []),
        "version": int(row.get("versionNumber") or 1),
        "first_posted_provisional": min(first) if first else None,
        "version_date": row.get("firstPublicationDate"),
        "version_history": versions, "publication_types": types,
        "withdrawn_or_removed": (any("withdraw" in value or "removal" in value for value in types)
                                 or row["title"].lower().lstrip().startswith(("withdrawn:", "withdrawn -", "removed:"))),
        "paper_url": "https://doi.org/" + doi if doi else f"https://europepmc.org/article/{row['source']}/{row['id']}",
        "index_url": f"https://europepmc.org/article/{row['source']}/{row['id']}",
        "retrieval_url": url,
        "linked_publication_records": row.get("commentCorrectionList", {}),
        "fulltext_urls": row.get("fullTextUrlList", {}).get("fullTextUrl", []),
    }


def collect(config, since, until, date_field, cache, log, raw_records, max_pages=200):
    for group, batch, query in queries(config, since, until, date_field):
        cursor = "*"
        retrieved = 0
        for page in range(max_pages):
            params = {"query": query, "format": "json", "resultType": "core", "pageSize": 1000,
                      "cursorMark": cursor}
            url = ENDPOINT + "?" + urllib.parse.urlencode(params)
            data = json.loads(sp.request(url, cache, "europepmc"))
            if "hitCount" not in data or "resultList" not in data:
                raise ValueError("Europe PMC response lacks counts/results")
            total = int(data["hitCount"])
            rows = data["resultList"].get("result", [])
            if not rows and retrieved < total:
                raise ValueError("Europe PMC returned an empty page before its advertised total")
            retrieved += len(rows)
            log.append({"source": "europepmc", "url": url, "group": group, "batch": batch,
                        "page": page, "total": total, "retrieved": len(rows), "date_field": date_field})
            for row in rows:
                key = (row["source"], row["id"])
                raw_records[key] = {**row, "_retrieval_url": url}
            if retrieved >= total:
                break
            next_cursor = data.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor:
                raise ValueError("Europe PMC cursor stopped before all results were retrieved")
            cursor = next_cursor
        else:
            raise RuntimeError(f"Europe PMC pagination cap reached for {group} batch {batch}")
        print(group, batch, "retrieved", retrieved, "total", total, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Defaults to the new source's checkpoint minus overlap, or 2023-01-01")
    parser.add_argument("--until", default=(dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)).isoformat())
    parser.add_argument("--date-field", choices=["first", "updated"], default="updated")
    parser.add_argument("--cache-dir")
    parser.add_argument("--output")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--check-research-square", nargs="+", help="Check original article metadata for selected DOIs instead of running discovery")
    args = parser.parse_args()
    config = json.loads((ROOT / "config/literature-keywords.json").read_text(encoding="utf-8"))
    state = json.loads((ROOT / "data/weekly-update-state.json").read_text(encoding="utf-8"))
    checkpoint = state.get("additional_sources", {}).get("europepmc_preprints", {}).get("last_successful_until")
    default_since = (dt.date.fromisoformat(checkpoint) - dt.timedelta(days=config["lookback_overlap_days"])).isoformat() if checkpoint else "2023-01-01"
    since = args.since or default_since
    if dt.date.fromisoformat(since) > dt.date.fromisoformat(args.until) or args.max_pages < 1:
        parser.error("Invalid date range or page limit")
    if dt.date.fromisoformat(args.until) >= dt.datetime.now(dt.timezone.utc).date():
        parser.error("--until must be a completed UTC day")
    cache = Path(args.cache_dir) if args.cache_dir else ROOT / ".cache/additional-preprints" / args.until
    cache.mkdir(parents=True, exist_ok=True)
    if args.check_research_square:
        results = []
        for doi in args.check_research_square:
            try:
                results.append(research_square_details(doi, cache))
            except Exception as error:
                results.append({"doi": doi, "status": "failed", "error": str(error)})
        destination = Path(args.output) if args.output else ROOT / ".cache/additional-preprint-status.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"status_checks": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return int(any(row["status"] == "failed" for row in results))
    records = {}
    log = []
    errors = []
    try:
        collect(config, since, args.until, args.date_field, cache, log, records, args.max_pages)
    except Exception as error:
        errors.append(type(error).__name__ + ": " + str(error))
    previous = sp.existing_entries()
    by_title = {}
    by_identity = {}
    for entry in previous:
        by_title.setdefault(entry["key"], []).append(entry)
        for url in entry["identity_urls"]:
            identity = sp.paper_identity(url)
            if identity:
                by_identity.setdefault(identity, []).append(entry)
    exclusions = json.loads((ROOT / "data/excluded-journal-identities.json").read_text(encoding="utf-8"))
    candidates = []
    for raw in records.values():
        record = parse_record(raw, raw.get("_retrieval_url", ENDPOINT))
        eligible, topics, methods = sp.topic_matches(record, config)
        if not eligible:
            continue
        matches = by_title.get(sp.normalized(record["title"]), [])
        matches = matches + by_identity.get(sp.paper_identity(record["doi"]), [])
        unique_matches = list({(entry["path"], entry["line"]): entry for entry in matches}.values())
        record.update(matched_topics=topics, matched_methods=methods,
                      existing_matches=sp.matching_existing(record, unique_matches),
                      journal_policy_exclusion=sp.journal_policy_exclusion(record, exclusions))
        candidates.append(record)
    status = {"status": "failed" if errors else "complete", "since": since, "until": args.until,
              "date_field": args.date_field, "retrieved_unique": len(records), "candidates": len(candidates),
              "errors": errors, "coverage": "Indexed preprints matching the recorded title/abstract queries. Index coverage and original server coverage are distinct."}
    payload = {"source_status": {"europepmc_preprints": status}, "retrievals": log,
               "records": list(records.values()), "candidates": candidates,
               "keyword_config": "config/literature-keywords.json",
               "keyword_sha256": hashlib.sha256((ROOT / "config/literature-keywords.json").read_bytes()).hexdigest()}
    destination = Path(args.output) if args.output else ROOT / ".cache/additional-preprint-candidates.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
