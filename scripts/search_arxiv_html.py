"""Official arXiv HTML supplement for explicit original-announcement date ranges.

This supplements failed Atom queries; it does not establish recent-revision coverage.
Full raw metadata is returned for re-screening. Admission and version-history review
remain separate. Uses only the Python standard library.
"""
import argparse
import calendar
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
import search_preprints as sp

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/arxiv-html'

class Node:

    def __init__(self, tag='', attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def all(self, predicate):
        found = [self] if predicate(self) else []
        for c in self.children:
            if isinstance(c, Node):
                found += c.all(predicate)
        return found

    def text(self):
        return ''.join((c.text() if isinstance(c, Node) else c for c in self.children))

class DOM(HTMLParser):

    def __init__(self):
        super().__init__()
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in ['br', 'hr', 'img', 'meta', 'link', 'input', 'wbr', 'source', 'area', 'embed']:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)

def cls(n, c):
    return c in n.attrs.get('class', '').split()

def clean(n):
    return re.sub('\\s+', ' ', n.text()).strip()

def parse(raw, url):
    dom = DOM()
    dom.feed(raw)
    rows = []
    for n in dom.root.all(lambda n: n.tag == 'li' and cls(n, 'arxiv-result')):
        get = lambda c: n.all(lambda n: cls(n, c))
        title = get('title')
        abstract = get('abstract-full')
        assert title and abstract
        aid = re.search('(\\d{4}\\.\\d{4,5})(?:v(\\d+))?', abstract[0].attrs['id'])
        assert aid
        ident = aid[1]
        version = int(aid[2] or 1)
        abstract_text = re.sub('\\s*[△▽]\\s*(Less|More)$', '', clean(abstract[0])).strip()
        full = clean(n)
        date = re.search('Submitted\\s+(\\d{1,2})\\s+(\\w+),\\s+(\\d{4})', full)
        assert date, (ident, full[-500:])
        month = list(calendar.month_name).index(date[2])
        updated = f'{date[3]}-{month:02d}-{int(date[1]):02d}'
        author_nodes = get('authors')
        authors = [clean(x) for x in author_nodes[0].all(lambda n: n.tag == 'a')] if author_nodes else []
        comments = get('comments')
        journal = get('journal-ref')
        doi_links = [x.attrs['href'] for x in n.all(lambda n: n.tag == 'a' and 'doi.org/' in n.attrs.get('href', ''))]
        rows.append({
            'source': 'arxiv',
            'id': ident,
            'version': version,
            'title': clean(title[0]),
            'abstract': abstract_text,
            'authors': authors,
            'first_posted': updated if version == 1 else None,
            'first_posted_requires_history': version > 1,
            'updated': updated,
            'year': int('20' + ident[:2]),
            'paper_url': f'https://arxiv.org/abs/{ident}v{version}',
            'doi': doi_links[0].split('doi.org/', 1)[1] if doi_links else '',
            'journal_ref': clean(journal[0]) if journal else '',
            'comment': re.sub('^Comments:\\s*', '', clean(comments[0])) if comments else '',
            'retrieval_url': url,
            'retrieval_basis': 'official_arxiv_advanced_search_html',
        })
    return rows

def fetch(url):
    f = CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.html')
    if f.exists():
        return f.read_text(encoding='utf-8')
    for attempt in range(3):
        time.sleep(3.2 if attempt == 0 else 15 * (attempt + 1))
        try:
            request = urllib.request.Request(
                url, headers={'User-Agent': 'AwesomeAIPathology-LiteratureMaintenance/1.0'})
            with urllib.request.urlopen(request, timeout=35) as response:
                raw = response.read().decode('utf-8')
            assert 'arxiv-result' in raw or 'Sorry, your query' in raw
            f.write_text(raw, encoding='utf-8')
            return raw
        except Exception:
            if attempt == 2:
                raise

def main():
    global CACHE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', required=True)
    parser.add_argument('--until', required=True)
    parser.add_argument('--terms', nargs='+', default=[
        'pathology', 'histopathology', 'histology', 'pathologist', 'whole slide', 'cytology'])
    parser.add_argument('--field', choices=['all', 'title'], default='all')
    parser.add_argument('--cache-dir', default=str(CACHE))
    parser.add_argument('--output', required=True)
    parser.add_argument('--max-pages', type=int, default=100)
    args = parser.parse_args()
    start = dt.date.fromisoformat(args.since)
    end = dt.date.fromisoformat(args.until)
    if start > end or end > dt.datetime.now(dt.timezone.utc).date() or args.max_pages < 1:
        parser.error('Invalid date range or page limit')
    CACHE = Path(args.cache_dir)
    CACHE.mkdir(parents=True, exist_ok=True)
    records = {}
    logs = []
    errors = []
    complete = False
    try:
        for page in range(args.max_pages):
            params = {
                'advanced': '',
                'classification-include_cross_list': 'include',
                'date-filter_by': 'date_range',
                'date-from_date': args.since,
                'date-to_date': args.until,
                'date-date_type': 'announced_date_first',
                'abstracts': 'show',
                'size': '200',
                'order': '-announced_date_first',
                'start': str(page * 200),
            }
            for i, t in enumerate(args.terms):
                params.update({
                    f'terms-{i}-operator': 'AND' if i == 0 else 'OR',
                    f'terms-{i}-term': t,
                    f'terms-{i}-field': args.field,
                })
            url = 'https://arxiv.org/search/advanced?' + urllib.parse.urlencode(params)
            raw = fetch(url)
            dom = DOM()
            dom.feed(raw)
            visible = clean(dom.root)
            match = re.search('Showing\\s+[\\d,]+\\s*[–-]\\s*[\\d,]+\\s+of\\s+([\\d,]+)', visible)
            if not match:
                raise ValueError('Missing advertised result count; do not interpret an unexpected page as zero results')
            total = int(match[1].replace(',', ''))
            rows = parse(raw, url)
            if len(rows) != min(200, total - page * 200):
                raise ValueError('Incomplete search page')
            logs.append({'source': 'arxiv', 'url': url, 'page': page, 'total': total, 'retrieved': len(rows), 'date_type': 'original_announcement'})
            for r in rows:
                old = records.get(r['id'])
                if old is None or (r['version'], r['updated']) > (old['version'], old['updated']):
                    records[r['id']] = r
            print('page', page, 'rows', len(rows), 'total', total, flush=True)
            if (page + 1) * 200 >= total:
                complete = True
                break
        if not complete:
            raise RuntimeError('Pagination limit reached; split queries or dates')
    except Exception as e:
        errors.append(type(e).__name__ + ': ' + str(e))
    config = json.loads((ROOT / 'config/literature-keywords.json').read_text(encoding='utf-8'))
    candidates = [r for r in records.values() if sp.topic_matches(r, config)[0]]
    data = {
        'source_status': {'arxiv': {
            'status': 'complete' if complete else 'failed',
            'mode': 'official_HTML_original_announcement_supplement',
            'since': args.since,
            'until': args.until,
            'terms': args.terms,
            'field': args.field,
            'retrieved_unique': len(records),
            'candidates': len(candidates),
            'errors': errors,
            'limitation': ('Completeness refers only to these query pages; older revised '
                           'papers require a separate updated-date search.'),
        }},
        'retrievals': logs,
        'records': list(records.values()),
        'candidates': candidates,
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(data['source_status']['arxiv'], flush=True)
    return 0 if complete else 1
if __name__ == '__main__':
    sys.exit(main())
