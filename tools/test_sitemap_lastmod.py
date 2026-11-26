"""Tests for tools/sitemap_lastmod.py. Run: python -m unittest tools/test_sitemap_lastmod.py -v
Each test builds a throwaway git repo with dated commits (no network, nothing is published)."""
import os, pathlib, re, subprocess, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sitemap_lastmod as S

PAGE = """<!doctype html><html><head><title>Guide</title><meta name="description" content="A guide">
<link rel="canonical" href="https://orynavo.com/p/"><link rel="alternate" hreflang="en" href="{hl}">
<script type="application/ld+json">{{"@type":"Article","dateModified":"{dm}","datePublished":"2026-01-01"}}</script>
<style>a{{color:red}}</style></head><body>
<header><a href="/">Orynavo</a></header><nav><a href="/x/">{nav}</a></nav>
<main><h1>Guide</h1><p>{body}</p><p>Data retrieved {stamp}.</p></main>
<footer><a href="/privacy.html">{foot}</a></footer><!-- {comment} --></body></html>"""
SM = '<?xml version="1.0" encoding="UTF-8"?>\r\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\r\n<url><loc>https://orynavo.com/p/</loc><lastmod>{d}</lastmod></url>\r\n</urlset>\r\n'
IDX = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<sitemap><loc>https://orynavo.com/sitemap-a.xml</loc><lastmod>2000-01-01</lastmod></sitemap>\n</sitemapindex>\n'


def page(**k):
    d = dict(hl="https://orynavo.com/p/", dm="2026-11-01", nav="Home", body="Original text.", stamp="1 Nov 2026", foot="Privacy", comment="c1"); d.update(k)
    return PAGE.format(**d)


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.r = pathlib.Path(self.tmp.name)
        self.g("init", "-q"); self.g("config", "user.email", "t@t"); self.g("config", "user.name", "t")
        (self.r / "p").mkdir()
        self.w("p/index.html", page()); self.w("sitemap-a.xml", SM.format(d="1999-01-01")); self.w("sitemap.xml", IDX)
        self.commit("2026-11-01", "init")

    def tearDown(self): self.tmp.cleanup()

    def g(self, *a):
        subprocess.run(["git", "-C", str(self.r), *a], check=True, capture_output=True)

    def w(self, rel, text): (self.r / rel).write_bytes(text.encode("utf-8"))

    def commit(self, date, msg):
        env = dict(os.environ, GIT_COMMITTER_DATE=date + "T12:00:00+00:00", GIT_AUTHOR_DATE=date + "T12:00:00+00:00")
        subprocess.run(["git", "-C", str(self.r), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.r), "commit", "-q", "-m", msg], check=True, capture_output=True, env=env)

    def lm(self, f="sitemap-a.xml"): return re.search(r"<lastmod>([^<]+)", (self.r / f).read_text()).group(1)

    def run_tool(self, today="2026-12-31", write=True):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): errs, detail, changed = S.run(self.r, today, write)
        return errs

    def test_initial_value_is_first_content_commit(self):
        self.assertEqual(self.run_tool(), []); self.assertEqual(self.lm(), "2026-11-01")

    def test_unchanged_content_keeps_lastmod_and_is_idempotent(self):
        self.run_tool(today="2026-11-05"); a = (self.r / "sitemap-a.xml").read_bytes(); i = (self.r / "sitemap.xml").read_bytes()
        self.run_tool(today="2026-12-31")   # later "build day", nothing changed
        self.assertEqual(a, (self.r / "sitemap-a.xml").read_bytes()); self.assertEqual(i, (self.r / "sitemap.xml").read_bytes())
        self.assertEqual(self.lm(), "2026-11-01")

    def test_header_footer_nav_hreflang_comment_change_does_not_bump(self):
        self.w("p/index.html", page(nav="Home and pricing", foot="Privacy and terms", comment="c2", hl="https://orynavo.com/p/?x=1"))
        self.commit("2026-11-10", "boilerplate only"); self.run_tool(); self.assertEqual(self.lm(), "2026-11-01")

    def test_sitemap_only_commit_does_not_bump(self):
        self.w("sitemap-a.xml", SM.format(d="2026-11-20")); self.commit("2026-11-20", "sitemap only"); self.run_tool(); self.assertEqual(self.lm(), "2026-11-01")

    def test_real_text_edit_bumps(self):
        self.w("p/index.html", page(body="Original text. A new paragraph with a real claim.")); self.commit("2026-11-12", "edit")
        self.run_tool(); self.assertEqual(self.lm(), "2026-11-12")

    def test_generated_timestamp_only_change_does_not_bump(self):
        self.w("p/index.html", page(dm="2026-11-15", stamp="15 Nov 2026")); self.commit("2026-11-15", "daily refresh, same data")
        self.run_tool(); self.assertEqual(self.lm(), "2026-11-01")

    def test_generated_timestamp_plus_real_data_change_bumps(self):
        self.w("p/index.html", page(dm="2026-11-16", stamp="16 Nov 2026", body="Original text. New notice added.")); self.commit("2026-11-16", "daily refresh, new notice")
        self.run_tool(); self.assertEqual(self.lm(), "2026-11-16")

    def test_uncommitted_generator_output_uses_today_only_if_content_changed(self):
        self.w("p/index.html", page(dm="2026-12-02", stamp="2 Dec 2026"))        # generator re-wrote stamps only
        self.run_tool(today="2026-12-02"); self.assertEqual(self.lm(), "2026-11-01")
        self.w("p/index.html", page(dm="2026-12-02", stamp="2 Dec 2026", body="Changed text."))  # real change, not yet committed
        self.run_tool(today="2026-12-02"); self.assertEqual(self.lm(), "2026-12-02")

    def test_index_lastmod_is_max_of_children(self):
        self.w("p/index.html", page(body="Edited.")); self.commit("2026-11-12", "edit"); self.run_tool()
        self.assertEqual(self.lm("sitemap.xml"), "2026-11-12")

    def test_only_lastmod_text_changes(self):
        before = (self.r / "sitemap-a.xml").read_bytes(); self.run_tool(); after = (self.r / "sitemap-a.xml").read_bytes()
        self.assertEqual(re.sub(rb"<lastmod>[^<]*", b"", before), re.sub(rb"<lastmod>[^<]*", b"", after)); self.assertIn(b"\r\n", after)

    def test_loc_without_file_is_an_error_and_nothing_is_written(self):
        t = SM.format(d="1999-01-01").replace("/p/", "/missing/"); self.w("sitemap-a.xml", t); self.commit("2026-11-02", "bad")
        self.assertTrue(self.run_tool()); self.assertEqual(self.lm(), "1999-01-01")

    def test_duplicate_loc_is_an_error(self):
        t = SM.format(d="1999-01-01").replace("</urlset>", '<url><loc>https://orynavo.com/p/</loc><lastmod>1999-01-01</lastmod></url>\r\n</urlset>')
        self.w("sitemap-a.xml", t); self.commit("2026-11-02", "dup"); self.assertTrue(self.run_tool())

    def test_rename_follows_history(self):
        (self.r / "q").mkdir(); self.g("mv", "p/index.html", "q/index.html")
        self.w("sitemap-a.xml", SM.format(d="1999-01-01").replace("/p/", "/q/")); self.commit("2026-11-18", "move")
        self.run_tool(); self.assertEqual(self.lm(), "2026-11-01")


if __name__ == "__main__":
    unittest.main()
