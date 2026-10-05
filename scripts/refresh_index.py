"""Refresh annual publication totals and README venue links without changing entries."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slug(title):
    return re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")


def main():
    annual = sorted((ROOT / "papers").glob("[0-9][0-9][0-9][0-9].md"), reverse=True)
    years = [int(p.stem) for p in annual]
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start = re.search(r"^# 20\d\d$", text, re.M)
    end = re.search(r"^# 2022$", text, re.M)
    if not start or not end or start.start() >= end.start():
        raise ValueError("Cannot identify annual README index boundaries")
    sections = []
    totals = 0
    for path in annual:
        year = int(path.stem)
        body = path.read_text(encoding="utf-8")
        venues, venue, count = [], None, 0
        for line in body.splitlines():
            if line.startswith("## "):
                if venue is not None:
                    venues.append((venue, count))
                venue, count = line[3:], 0
            elif line.startswith("- ") and "[[paper]" in line:
                if venue is None:
                    raise ValueError(f"Paper without venue heading: {path}")
                count += 1
        if venue is not None:
            venues.append((venue, count))
        if len({v for v, _ in venues}) != len(venues):
            raise ValueError(f"Duplicate venue heading: {path}")
        total = sum(n for _, n in venues)
        totals += total
        body, replacements = re.subn(r"\*\*[\d,]+ publications\*\*, organized by journal and conference\.",
                                     f"**{total:,} publications**, organized by journal and conference.", body, count=1)
        if replacements != 1:
            raise ValueError(f"Missing annual total: {path}")
        body = re.sub(r"^\[Back to collection\].*$", "[Back to collection](../README.md#papers) · " +
                      " · ".join(f"[{y}]({y}.md)" for y in years if y != year), body, count=1, flags=re.M)
        path.write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")
        sections.extend([f"# {year}", "", f"**{total:,} publications** · [Browse the complete {year} list](papers/{year}.md)", ""])
        sections.extend(f"- [{v}](papers/{year}.md#{slug(v)}) ({n})" for v, n in venues)
        sections.extend(["", "---", ""])
        print(year, total)
    suffix = text[end.start():]
    totals += sum(l.startswith("- ") and "[[paper]" in l for l in suffix.splitlines())
    prefix = text[:start.start()]
    prefix = re.sub(r"- 📚 [\d,]+\+? curated (?:papers|publication entries).*", f"- 📚 {totals:,} curated publication entries in computational pathology and tissue omics", prefix)
    prefix = re.sub(r"^- \[20\d\d\]\(papers/20\d\d.md\).*", "- " + " · ".join(f"[{y}](papers/{y}.md)" for y in years), prefix, count=1, flags=re.M)
    readme.write_text(prefix + "\n".join(sections) + "\n" + suffix, encoding="utf-8", newline="\n")
    print("Total publication entries:", totals)


if __name__ == "__main__":
    main()
