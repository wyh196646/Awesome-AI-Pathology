"""Collect review candidates from official APIs; never edit the bibliography or checkpoint.

Python 3.10+, standard library only. See docs/weekly-maintenance.md.
"""
import argparse
import datetime as dt
import functools
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/",
      "x": "http://arxiv.org/schemas/atom"}
LAST_REQUEST = {}


def normalized(text):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", html.unescape(text)).lower())


def searchable(text):
    return re.sub(r"[^a-z0-9*]+", " ", unicodedata.normalize("NFKD", html.unescape(text)).lower()).strip()


@functools.lru_cache(maxsize=None)
def term_pattern(term):
    words = searchable(term).split()
    return re.compile(r"\b" + r"\s+".join(re.escape(w).replace(r"\*", r"[a-z0-9]*") for w in words) + r"\b")


def topic_matches(record, config):
    text = searchable(record["title"] + " " + record.get("abstract", ""))
    groups = {g: [t for t in terms if term_pattern(t).search(text)]
              for g, terms in config["topic_groups"].items()}
    methods = [t for t in config["method_terms"] if term_pattern(t).search(text)]
    cancer = any(term_pattern(t).search(text) for t in config["cancer_terms"])
    biological = any(term_pattern(t).search(text) for t in config["biological_context_terms"])
    # These rules are candidate retrieval, not final inclusion decisions.
    eligible = biological and bool(groups["histology_cytology"] or groups["spatial_omics"] or
                    (groups["single_cell"] and methods) or
                    (groups["tissue_microenvironment"] and methods) or
                    (groups["cancer_multimodal_omics"] and methods and cancer))
    return eligible, {g: values for g, values in groups.items() if values}, methods


def existing_entries():
    entries = []
    for path in [ROOT / "README.md", *sorted((ROOT / "papers").glob("*.md"))]:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("- ") or "[[paper]" not in line:
                continue
            title = line[2:].split("[[paper]", 1)[0].strip()
            match = re.search(r"\[\[paper\]\((.*?)\)\]", line)
            url = urllib.parse.unquote(match.group(1)) if match else ""
            identity_urls = [urllib.parse.unquote(u) for u in re.findall(
                r"\[\[(?:paper|preprint|arxiv|biorxiv|medrxiv)\]\((.*?)\)\]", line, re.I)]
            entries.append({"title": title, "key": normalized(title), "paper_url": url,
                            "identity_urls": identity_urls,
                            "path": str(path.relative_to(ROOT)).replace("\\", "/"), "line": number})
    return entries


@functools.lru_cache(maxsize=16384)
def paper_identity(value):
    value = urllib.parse.unquote(html.unescape(value)).strip().lower()
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme in ("http", "https"):
        host = parsed.hostname or ""
        path = parsed.path.lstrip("/")
        if host in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
            if not path.startswith(("abs/", "pdf/")):
                return None
            value = path.split("/", 1)[1].removesuffix(".pdf")
        elif host in ("doi.org", "dx.doi.org", "www.doi.org"):
            value = path
        elif host in ("biorxiv.org", "www.biorxiv.org", "medrxiv.org", "www.medrxiv.org"):
            if not path.startswith("content/"):
                return None
            value = path[len("content/"):]
            value = re.sub(r"(?:\.full(?:\.pdf)?|\.abstract|/pdf)$", "", value)
            value = re.sub(r"v\d+$", "", value)
        else:
            return None
    value = re.sub(r"^(?:arxiv|doi):\s*", "", value)
    if re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-z][a-z0-9.\-]*/\d{7})(?:v\d+)?", value):
        return "arxiv", re.sub(r"v\d+$", "", value)
    if re.fullmatch(r"10\.\d{4,9}/\S+", value):
        return "doi", value
    return None


def matching_existing(record, previous):
    key = normalized(record["title"])
    identifiers = {paper_identity(str(value)) for value in
                   (record["id"], record.get("doi"), record.get("published_doi"))
                   if value not in (None, "", "NA")}
    identifiers.discard(None)
    return [entry for entry in previous if entry["key"] == key or
            any(paper_identity(url) in identifiers
                for url in entry.get("identity_urls", [entry["paper_url"]]))]


def journal_policy_exclusion(record, exclusions):
    """Flag known excluded formal publications for screening; do not delete candidates."""
    title_hash = hashlib.sha256(normalized(record["title"]).encode()).hexdigest()
    identifiers = {paper_identity(str(value)) for value in
                   (record["id"], record.get("doi"), record.get("published_doi"))
                   if value not in (None, "", "NA")}
    identifiers.discard(None)
    if (title_hash in exclusions["title_sha256"] or
            any(f"{kind}:{value}" in exclusions["identifiers"] for kind, value in identifiers)):
        return "Known formal journal publication removed by the CAS major-zone-1/SCIE policy"
    return None


def request(url, cache, source):
    destination = cache / (hashlib.sha256(url.encode()).hexdigest() + ".response")
    if destination.exists():
        return destination.read_bytes()
    delay = 3.1 if source == "arxiv" else 0.4
    for attempt in range(4):
        time.sleep(max(0, delay - (time.monotonic() - LAST_REQUEST.get(source, 0))))
        LAST_REQUEST[source] = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AwesomeAIPathology-LiteratureMaintenance/1.0"})
            with urllib.request.urlopen(req, timeout=50) as response:
                data = response.read()
            # Refuse cached HTML error pages masquerading as successful metadata.
            if data.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                raise ValueError("API returned HTML rather than bibliographic metadata")
            destination.write_bytes(data)
            return data
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)


def arxiv_records(config, since, until, cache, log):
    records = {}
    page_size = config["arxiv_page_size"]
    for group, terms in config["topic_groups"].items():
        clauses = []
        for term in terms:
            value = term if " " not in term else '"' + term + '"'
            clauses.append(f"ti:{value} OR abs:{value}")
        query = "(" + " OR ".join(clauses) + ")"
        complete = False
        for page in range(config["arxiv_max_pages_per_group"]):
            params = {"search_query": query, "start": page * page_size, "max_results": page_size,
                      "sortBy": "lastUpdatedDate", "sortOrder": "descending"}
            url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
            feed = ET.fromstring(request(url, cache, "arxiv"))
            total_node = feed.find("o:totalResults", NS)
            if total_node is None:
                raise ValueError("arXiv response missing totalResults")
            total = int(total_node.text)
            entries = feed.findall("a:entry", NS)
            if total > page * page_size and not entries:
                raise ValueError("arXiv returned an empty page before the advertised total")
            log.append({"source": "arxiv", "group": group, "url": url, "total": total,
                        "page": page, "retrieved": len(entries)})
            reached_since = False
            for node in entries:
                value = lambda name: " ".join((node.findtext(name, "", NS) or "").split())
                identifier = value("a:id").rsplit("/abs/", 1)[-1]
                if identifier.endswith("errors") or identifier.startswith("http"):
                    raise ValueError("arXiv returned an error entry")
                updated = value("a:updated")[:10]
                published = value("a:published")[:10]
                if not updated or not published:
                    raise ValueError("arXiv entry has no publication/update date")
                if updated < since:
                    reached_since = True
                    continue
                if updated > until:
                    continue
                base_id = re.sub(r"v\d+$", "", identifier)
                version = re.search(r"v(\d+)$", identifier)
                record = {"source": "arxiv", "id": base_id, "version": int(version.group(1)) if version else 1,
                          "title": value("a:title"), "abstract": value("a:summary"),
                          "authors": [" ".join((n.text or "").split()) for n in node.findall("a:author/a:name", NS)],
                          "first_posted": published, "updated": updated, "year": int(published[:4]),
                          "paper_url": "https://arxiv.org/abs/" + base_id, "doi": value("x:doi"),
                          "journal_ref": value("x:journal_ref"), "comment": value("x:comment"),
                          "categories": [n.get("term") for n in node.findall("a:category", NS)], "retrieval_url": url}
                records[base_id] = record
            if reached_since or (page + 1) * page_size >= total:
                complete = True
                break
        if not complete:
            raise RuntimeError(f"arXiv pagination cap reached for {group}; split query/window and rerun")
    return list(records.values())


def rxiv_records(source, since, until, cache, log):
    records = {}
    cursor = 0
    while True:
        url = f"https://api.biorxiv.org/details/{source}/{since}/{until}/{cursor}/json"
        data = json.loads(request(url, cache, source))
        messages = data.get("messages") or []
        if not messages:
            raise ValueError(f"{source}: missing API status")
        message = messages[0]
        status = str(message.get("status", "")).lower()
        if status not in ("ok", "no papers found"):
            raise ValueError(f"{source}: API status {status!r}")
        collection = data.get("collection", [])
        if status == "ok" and "total" not in message:
            raise ValueError(f"{source}: missing total; interval completeness is unknown")
        total = int(message.get("total", 0))
        if total < 0 or cursor + len(collection) > total:
            raise ValueError(f"{source}: inconsistent pagination total")
        if not collection and cursor < total:
            raise ValueError(f"{source}: empty page before advertised total")
        log.append({"source": source, "url": url, "cursor": cursor, "total": total,
                    "retrieved": len(collection)})
        for item in collection:
            doi = item.get("doi", "").lower()
            posted = item.get("date", "")
            if not doi or not posted or not item.get("title"):
                raise ValueError(f"{source}: incomplete bibliographic record")
            if not since <= posted <= until:
                raise ValueError(f"{source}: returned date outside requested interval: {posted}")
            version = int(item.get("version", 1))
            record = {"source": source, "id": doi, "doi": doi, "version": version,
                      "title": html.unescape(item["title"]), "abstract": html.unescape(item.get("abstract", "")),
                      "authors": item.get("authors", ""), "posted": posted, "updated": posted,
                      "year": int(posted[:4]), "paper_url": f"https://www.{source}.org/content/{doi}v{version}",
                      "published_doi": item.get("published", ""), "category": item.get("category", ""),
                      "retrieval_url": url}
            if doi not in records or version > records[doi]["version"]:
                records[doi] = record
        cursor += len(collection)
        if cursor >= total:
            break
        if not collection:
            raise ValueError(f"{source}: pagination made no progress")
    return list(records.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Override all source start dates (YYYY-MM-DD)")
    parser.add_argument("--until", default=(dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)).isoformat())
    parser.add_argument("--sources", nargs="+", choices=["arxiv", "biorxiv", "medrxiv"])
    parser.add_argument("--output", default=str(ROOT / ".cache" / "preprint-candidates.json"))
    args = parser.parse_args()
    config = json.loads((ROOT / "config/literature-keywords.json").read_text(encoding="utf-8"))
    state = json.loads((ROOT / "data/weekly-update-state.json").read_text(encoding="utf-8"))
    until_date = dt.date.fromisoformat(args.until)
    if until_date > dt.datetime.now(dt.timezone.utc).date():
        parser.error("--until cannot be in the future")
    cache = ROOT / ".cache" / "preprint-api" / args.until
    cache.mkdir(parents=True, exist_ok=True)
    previous = existing_entries()
    exclusions = json.loads((ROOT / "data/excluded-journal-identities.json").read_text(encoding="utf-8"))
    exclusions = {"title_sha256": set(exclusions["title_sha256"]),
                  "identifiers": set(exclusions["identifiers"])}
    candidates, retrievals, source_status = [], [], {}
    for source in args.sources or config["sources"]:
        checkpoint = state["sources"][source]["last_successful_until"]
        since = args.since or ((dt.date.fromisoformat(checkpoint) -
                                dt.timedelta(days=config["lookback_overlap_days"])).isoformat()
                               if checkpoint else state["bootstrap_since"])
        if dt.date.fromisoformat(since) > until_date:
            parser.error(f"{source}: --since must be no later than --until")
        print(f"Searching {source}: {since} to {args.until}", flush=True)
        try:
            records = (arxiv_records(config, since, args.until, cache, retrievals) if source == "arxiv"
                       else rxiv_records(source, since, args.until, cache, retrievals))
            count = 0
            for record in records:
                eligible, groups, methods = topic_matches(record, config)
                if not eligible:
                    continue
                record["matched_topics"], record["matched_methods"] = groups, methods
                record["existing_matches"] = matching_existing(record, previous)
                record["journal_policy_exclusion"] = journal_policy_exclusion(record, exclusions)
                candidates.append(record)
                count += 1
            source_status[source] = {"status": "complete", "since": since, "until": args.until,
                                     "retrieved_unique": len(records), "candidates": count}
            print(f"{source}: {len(records)} unique records, {count} candidates", flush=True)
        except Exception as error:
            source_status[source] = {"status": "failed", "since": since, "until": args.until,
                                     "error": f"{type(error).__name__}: {error}"}
            print(f"{source}: FAILED: {error}", flush=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "keyword_config": "config/literature-keywords.json",
                                 "keyword_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                                 "keyword_config_snapshot": config, "source_status": source_status,
                                 "retrievals": retrievals, "candidates": candidates}, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"Wrote {len(candidates)} candidates to {output}", flush=True)
    return 1 if any(s["status"] != "complete" for s in source_status.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
