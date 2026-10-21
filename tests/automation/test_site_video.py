"""The intro video on the site: invariants that `mkdocs build --strict` cannot check.

MkDocs neither rewrites nor validates paths inside raw HTML, so a typo in a poster, a source or the
deploy step would ship silently. These tests read the landing template (overrides/home.html), the
Overview (docs/overview.md) and the docs deploy workflow; no build, no network.
"""

from __future__ import annotations

import posixpath
import re
import unittest
from html.parser import HTMLParser

from .helpers import REPO

DOCS = REPO / "docs"
DEPLOY = REPO / ".github" / "workflows" / "deploy-docs.yml"
# Each page that embeds the video, and the folder its built page lives in, from the site root:
# the landing page is the root itself, the Overview builds as overview/index.html.
PAGES = {"overrides/home.html": "", "docs/overview.md": "overview/"}
# {{ 'assets/x' | url }} in a template: a path from the site root, which MkDocs makes relative.
URL_FILTER = re.compile(r"""^\{\{\s*['"]([^'"]+)['"]\s*\|\s*url\s*\}\}(.*)$""")
RELEASE_LINK = re.compile(r"/releases/download/([^/]+)/([^/?#]+)$")


class _Page(HTMLParser):
    """The <video> elements of a page with their <source> children, its links and its ids."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.videos: list[dict] = []
        self.links: list[str] = []
        self.ids: set[str] = set()
        self._video: dict | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "video":
            self._video = {"attrs": a, "sources": []}
            self.videos.append(self._video)
        elif tag == "source" and self._video is not None:
            self._video["sources"].append(a)
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "video":
            self._video = None


def site_path(ref: str, page_dir: str) -> str | None:
    """Where a reference on a page points, as a path from the site root; None for another site."""
    ref = ref.strip()
    m = URL_FILTER.match(ref)
    if m:
        path = m.group(1) + m.group(2)
    elif re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", ref, re.IGNORECASE):
        return None
    else:
        path = posixpath.join(page_dir, ref)
    return posixpath.normpath(path.split("#", 1)[0].split("?", 1)[0])


class SiteVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for rel, page_dir in PAGES.items():
            page = _Page()
            page.feed((REPO / rel).read_text(encoding="utf-8"))
            page.close()
            cls.pages[rel] = (page_dir, page)
        cls.deploy = DEPLOY.read_text(encoding="utf-8")

    def videos(self):
        for rel, (page_dir, page) in self.pages.items():
            for video in page.videos:
                yield rel, page_dir, video

    @staticmethod
    def played(page_dir: str, video: dict) -> list[str | None]:
        """The site paths a <video> plays: its src, or the src of its <source> children."""
        refs = [video["attrs"]["src"]] if video["attrs"].get("src") else []
        refs += [s["src"] for s in video["sources"] if s.get("src")]
        return [site_path(ref, page_dir) for ref in refs]

    def fetch(self) -> tuple[str, str, str]:
        """Tag, file pattern and folder of the deploy's `gh release download`."""
        text = self.deploy.replace("\\\n", " ")
        m = re.search(r"gh release download\s+(\S+)(.*)", text)
        self.assertIsNotNone(m, "deploy-docs.yml runs no `gh release download`")
        args = m.group(2)
        pattern = re.search(r"(?:--pattern|-p)\s+([^\s;]+)", args)
        folder = re.search(r"(?:--dir|-D)\s+([^\s;]+)", args)
        self.assertIsNotNone(pattern, "the download names no --pattern")
        self.assertIsNotNone(folder, "the download names no --dir")
        return m.group(1), pattern.group(1), folder.group(1).rstrip("/")

    def test_each_page_embeds_the_video(self):
        for rel, (_, page) in self.pages.items():
            with self.subTest(page=rel):
                self.assertGreaterEqual(len(page.videos), 1, f"{rel} has no <video>")

    def test_nothing_loads_or_plays_before_a_press(self):
        for rel, _, video in self.videos():
            a = video["attrs"]
            with self.subTest(page=rel):
                self.assertEqual(a.get("preload"), "none")
                self.assertNotIn("autoplay", a)
                self.assertIn("controls", a)
                self.assertIn("playsinline", a)
                self.assertTrue(a.get("aria-label"), "the player needs an accessible name")

    def test_posters_exist(self):
        for rel, page_dir, video in self.videos():
            with self.subTest(page=rel):
                poster = site_path(video["attrs"].get("poster", ""), page_dir)
                self.assertRegex(poster or "", r"^assets/video/[^/]+\.(?:jpg|jpeg|png|webp)$")
                self.assertTrue((DOCS / poster).is_file(), f"{rel}: the poster docs/{poster} is missing")

    def test_sources_are_under_assets_video(self):
        for rel, page_dir, video in self.videos():
            with self.subTest(page=rel):
                paths = self.played(page_dir, video)
                self.assertTrue(paths, f"{rel}: the <video> has no src")
                for path in paths:
                    self.assertRegex(path or "", r"^assets/video/[^/]+\.mp4$")

    def test_the_deploy_fetches_what_the_pages_play(self):
        _, pattern, folder = self.fetch()
        self.assertEqual(folder, "docs/assets/video")
        for rel, page_dir, video in self.videos():
            for path in self.played(page_dir, video):
                with self.subTest(page=rel, src=path):
                    self.assertEqual("docs/" + path, f"{folder}/{pattern}")

    def test_the_fetch_runs_before_the_build(self):
        fetch, build = self.deploy.find("gh release download"), self.deploy.find("mkdocs build")
        self.assertTrue(0 <= fetch < build, "the video must be downloaded before mkdocs build")

    def test_release_links_name_the_fetched_asset(self):
        tag, pattern, _ = self.fetch()
        links = [(rel, href) for rel, (_, page) in self.pages.items() for href in page.links
                 if RELEASE_LINK.search(href)]
        self.assertTrue(links, "no fallback link to the release asset")
        for rel, href in links:
            with self.subTest(page=rel, href=href):
                self.assertEqual(RELEASE_LINK.search(href).groups(), (tag, pattern))

    def test_the_landing_link_reaches_the_overview_video(self):
        _, home = self.pages["overrides/home.html"]
        _, overview = self.pages["docs/overview.md"]
        hrefs = [href for href in home.links if href.endswith("#intro-video")]
        self.assertTrue(hrefs, "the landing page has no link to overview/#intro-video")
        for href in hrefs:
            self.assertEqual(site_path(href, ""), "overview")
        self.assertIn("intro-video", overview.ids)

    def test_the_video_stays_out_of_git(self):
        rules = [line.strip() for line in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()]
        self.assertIn("docs/assets/video/*.mp4", rules)

    def test_overview_paths_assume_directory_urls(self):
        # The Overview's ../ paths hold only while it builds as overview/index.html.
        config = (REPO / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertNotRegex(config, r"(?mi)^use_directory_urls:\s*(?:false|no|off)\b")


if __name__ == "__main__":
    unittest.main()
