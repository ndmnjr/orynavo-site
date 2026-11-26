#!/usr/bin/env python3
"""Set every sitemap <lastmod> on orynavo.com to the date the page's CONTENT last substantially changed.

Rule (never build date, never file mtime):
  1. Take the page's git history (git log --follow). For every version compute a NORMALISED fingerprint:
     title, meta description/robots, canonical, JSON-LD (with dateModified/datePublished removed) and the
     visible text of <body> with header, footer, nav, aside, scripts, styles, svg, comments, hreflang links
     and visible "updated/generated <date>" stamps removed.
  2. lastmod = committer date of the newest commit whose fingerprint differs from the previous version
     (first commit counts). Commits that only touch boilerplate, sitemaps, hreflang, comments, link hrefs or
     date stamps do not move it.
  3. Uncommitted working-tree content (a generator just wrote the file) is compared with HEAD: if the
     fingerprint differs it is a real change dated --today, otherwise HEAD's content date is kept.
     A new untracked page gets its own dateModified when valid (<= today), else --today.
  4. The page's own dateModified / visible "updated" stamp is only a cross-check, reported when it disagrees
     (generators bump it daily without a content change, so it is not trusted over git).
  5. Sitemap index lastmod = max lastmod of the child sitemap's URLs (recursive).
Only the <lastmod> text is rewritten; everything else (loc order, newlines, priority/changefreq) stays
byte-identical. Idempotent: a second run changes nothing.

Usage: python tools/sitemap_lastmod.py [--root DIR] [--today YYYY-MM-DD] [--write] [--json report.json]
Without --write it is a dry run that prints the diff summary. Exit 2 on validation errors.
"""
import argparse, datetime, hashlib, json, pathlib, re, subprocess, sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

HOST = "https://orynavo.com"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
SKIP_TAGS = {"script", "style", "svg", "noscript", "header", "footer", "nav", "aside", "template", "head"}
STAMP = re.compile(r"(?i)\b(?:last\s+)?(?:updated|refreshed|generated|retrieved|fetched|data as of|as of|checked)\b[:\s]*(?:on\s+)?"
                   r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})(?:[ T]\d{2}:\d{2}(?::\d{2})?(?:\s*(?:UTC|Z))?)?")
ISO_TS = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
DATE_KEYS = {"datemodified", "datepublished"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0; self.parts = []; self.in_title = False; self.title = []; self.meta = []; self.ld = []; self._ld = False; self._ldbuf = []
        self.in_head_skip = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title": self.in_title = True
        elif tag == "meta":
            n = (a.get("name") or a.get("property") or "").lower()
            if n in ("description", "robots", "og:title", "og:description"): self.meta.append((n, a.get("content", "")))
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical": self.meta.append(("canonical", a.get("href", "")))
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json": self._ld = True; self._ldbuf = []
        if tag in SKIP_TAGS and tag != "head": self.skip += 1

    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "script" and self._ld:
            self._ld = False; self.ld.append("".join(self._ldbuf))
        if tag in SKIP_TAGS and tag != "head" and self.skip: self.skip -= 1

    def handle_data(self, d):
        if self.in_title: self.title.append(d)
        elif self._ld: self._ldbuf.append(d)
        elif not self.skip: self.parts.append(d)


def _strip_dates(o):
    if isinstance(o, dict): return {k: _strip_dates(v) for k, v in o.items() if k.lower() not in DATE_KEYS}
    if isinstance(o, list): return [_strip_dates(v) for v in o]
    return o


def normalize(html):
    """Fingerprint-able text of what a reader/crawler sees as the page's content (boilerplate and stamps removed)."""
    p = _Text()
    try: p.feed(html)
    except Exception: pass
    ld = []
    for raw in p.ld:
        try: ld.append(json.dumps(_strip_dates(json.loads(raw)), sort_keys=True, ensure_ascii=False))
        except Exception: ld.append(ISO_TS.sub("", raw))
    text = " ".join("".join(p.parts).split())
    head = "|".join([" ".join("".join(p.title).split())] + [f"{k}={v}" for k, v in sorted(p.meta)])
    out = head + "\n" + "\n".join(sorted(ld)) + "\n" + text
    out = STAMP.sub("", out); out = ISO_TS.sub("", out)
    return " ".join(out.split(" ")) if False else re.sub(r"[ \t]+", " ", out)


def fp(html):
    return hashlib.sha256(normalize(html).encode("utf-8")).hexdigest()


def page_stamps(html):
    """dateModified values and visible 'updated' stamps found in the page (cross-check only)."""
    out = set(re.findall(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', html))
    for m in re.finditer(r"(?i)\b(?:last\s+)?updated\b[:\s]*(?:on\s+)?(\d{4}-\d{2}-\d{2})", re.sub(r"<[^>]+>", " ", html)):
        out.add(m.group(1))
    return sorted(out)


class Repo:
    """One `git log` + one persistent `git cat-file --batch` instead of a process per file/commit."""
    def __init__(self, root):
        self.root = root; self.chains = {}; self.cat = None
        out = subprocess.run(["git", "-C", str(root), "log", "-M", "--name-status", "--format=@@%H %cs", "--no-merges"], capture_output=True).stdout.decode("utf-8", "replace") if True else ""
        self.commits = []   # newest first: (hash, date, [(status, old, new)])
        cur = None
        for line in out.splitlines():
            if line.startswith("@@"): cur = (line[2:].split()[0], line[2:].split()[1], []); self.commits.append(cur)
            elif line.strip() and cur:
                f = line.split("\t")
                if f[0].startswith("R"): cur[2].append(("R", f[1], f[2]))
                else: cur[2].append((f[0][0], None, f[-1]))

    def history(self, rel):
        """[(commit, date, path_at_commit)] oldest -> newest, following renames and ignoring deletes."""
        if rel in self.chains: return self.chains[rel]
        path = rel; res = []
        for h, d, ch in self.commits:
            for st, old, new in ch:
                if new == path and st != "D":
                    res.append((h, d, path))
                    if st == "R": path = old
                    break
        self.chains[rel] = res[::-1]
        return self.chains[rel]

    def blob(self, commit, path):
        if self.cat is None: self.cat = subprocess.Popen(["git", "-C", str(self.root), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.cat.stdin.write(f"{commit}:{path}\n".encode()); self.cat.stdin.flush()
        head = self.cat.stdout.readline().split()
        if len(head) < 3 or head[1] != b"blob": return None
        n = int(head[2]); data = self.cat.stdout.read(n); self.cat.stdout.read(1)
        return data.decode("utf-8", "replace")

    def close(self):
        if self.cat: self.cat.stdin.close(); self.cat.wait(); self.cat.stdout.close(); self.cat = None


def is_repo(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"], capture_output=True).returncode == 0


def loc_to_file(root, loc):
    if not loc.startswith(HOST + "/"): return None
    p = loc[len(HOST) + 1:]
    cands = [p + "index.html"] if (p == "" or p.endswith("/")) else [p, p + "/index.html", p + ".html"]
    for c in cands:
        if (root / c).is_file(): return c
    return None


def content_date(repo, root, rel, today):
    """-> (date, reason, stamps)"""
    cur = (root / rel).read_bytes().decode("utf-8", "replace")
    stamps = page_stamps(cur)
    h = repo.history(rel)
    last_date = last_commit = prev = None
    for c, d, path in h:
        blob = repo.blob(c, path)
        if blob is None: continue
        x = fp(blob)
        if x != prev: last_date, last_commit = d, c
        prev = x
    if prev is None:
        valid = [s for s in stamps if s <= today]
        return (max(valid) if valid else today), "new untracked page (own dateModified/stamp or today)", stamps
    if fp(cur) != prev:
        return today, "uncommitted real content change in working tree", stamps
    return last_date, f"last content change in commit {last_commit[:7]}", stamps


def read_sitemap(path):
    t = path.read_bytes().decode("utf-8")
    root = ET.fromstring(t)
    kind = "index" if root.tag == NS + "sitemapindex" else "urlset"
    items = []
    for e in root:
        loc = e.find(NS + "loc"); lm = e.find(NS + "lastmod")
        items.append((loc.text.strip() if loc is not None else None, lm.text.strip() if lm is not None else None))
    return t, kind, items


def rewrite(text, new):
    """Replace only <lastmod> inside each <url>/<sitemap> block whose loc is in `new`. Returns new text."""
    def blk(m):
        b = m.group(0); loc = re.search(r"<loc>([^<]+)</loc>", b)
        if not loc or loc.group(1).strip() not in new: return b
        v = new[loc.group(1).strip()]
        if "<lastmod>" in b: return re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{v}</lastmod>", b)
        return b  # never add elements that were not there
    return re.sub(r"<(url|sitemap)>.*?</\1>", blk, text, flags=re.S)


def run(root, today, write=False, report=None):
    root = pathlib.Path(root).resolve()
    maps = sorted(p for p in root.rglob("sitemap*.xml") if ".git" not in p.parts and not p.relative_to(root).parts[0].startswith("_"))  # top-level _dirs (review copies) are ignored
    errors, info = [], {}
    repo = Repo(root)
    for p in maps:
        rel = p.relative_to(root).as_posix()
        try: t, kind, items = read_sitemap(p)
        except Exception as e: errors.append(f"{rel}: invalid XML: {e}"); continue
        locs = [l for l, _ in items]
        if len(set(locs)) != len(locs): errors.append(f"{rel}: duplicate <loc>")
        info[rel] = dict(text=t, kind=kind, items=items)
    cache = {}; new_all = {}; detail = {}
    # 1. urlsets
    for rel, d in info.items():
        if d["kind"] != "urlset": continue
        new = {}
        for loc, old in d["items"]:
            f = loc_to_file(root, loc)
            if f is None:
                errors.append(f"{rel}: <loc> {loc} does not map to a file in the tree"); continue
            if f not in cache: cache[f] = content_date(repo, root, f, today)
            nd, why, stamps = cache[f]
            new[loc] = nd
            detail.setdefault(rel, []).append(dict(loc=loc, file=f, old=old, new=nd, reason=why, stamps=stamps))
        new_all[rel] = new
    # 2. indexes (children resolved recursively)
    def max_of(rel, seen=()):
        d = info.get(rel)
        if d is None: return None
        if d["kind"] == "urlset": return max(new_all.get(rel, {}).values(), default=None)
        vals = []
        for loc, _ in d["items"]:
            ch = loc[len(HOST) + 1:] if loc.startswith(HOST + "/") else None
            if ch is None or ch not in info: errors.append(f"{rel}: child sitemap {loc} not in tree"); continue
            if ch in seen: continue
            vals.append(max_of(ch, seen + (rel,)))
        return max([v for v in vals if v], default=None)
    for rel, d in info.items():
        if d["kind"] != "index": continue
        new = {}
        for loc, old in d["items"]:
            ch = loc[len(HOST) + 1:] if loc.startswith(HOST + "/") else None
            nd = max_of(ch) if ch in info else None
            if nd: new[loc] = nd; detail.setdefault(rel, []).append(dict(loc=loc, file=ch, old=old, new=nd, reason="max lastmod of child sitemap", stamps=[]))
        new_all[rel] = new
    repo.close()
    changed = {}
    for rel, d in info.items():
        out = rewrite(d["text"], new_all.get(rel, {}))
        try: ET.fromstring(out)
        except Exception as e: errors.append(f"{rel}: result is not valid XML: {e}"); continue
        if out != d["text"]:
            changed[rel] = sum(1 for x in detail.get(rel, []) if x["old"] != x["new"])
            if write and not errors: (root / rel).write_bytes(out.encode("utf-8"))
    # report
    for rel in sorted(info):
        rows = detail.get(rel, [])
        diff = [r for r in rows if r["old"] != r["new"]]
        print(f"{rel}: {len(rows)} entries, {len(diff)} lastmod change(s); distinct before={len({r['old'] for r in rows})} after={len({r['new'] for r in rows})}")
    mism = [(r["loc"], r["new"], r["stamps"]) for rows in detail.values() for r in rows if r["stamps"] and r["new"] not in r["stamps"] and r["file"].endswith(".html")]
    if mism: print(f"note: {len(mism)} page(s) whose own dateModified/updated stamp differs from the content-change date (git wins; stamps not trusted)")
    for e in errors: print("ERROR:", e)
    print("mode:", "WRITE" if write and not errors else "dry-run", "| files that would change/changed:", len(changed))
    if report: pathlib.Path(report).write_text(json.dumps(dict(today=today, detail=detail, errors=errors, stamp_mismatch=mism), indent=1), encoding="utf-8")
    return errors, detail, changed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--today", default=datetime.date.today().isoformat(), help="date given to uncommitted real content changes")
    ap.add_argument("--write", action="store_true"); ap.add_argument("--json")
    a = ap.parse_args()
    errs, _, _ = run(a.root, a.today, a.write, a.json)
    sys.exit(2 if errs else 0)
