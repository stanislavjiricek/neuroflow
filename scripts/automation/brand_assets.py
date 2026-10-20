#!/usr/bin/env python3
"""brand_assets.py: the neuroflow ring, one generator for every brand image in docs/assets/brand/.

The shapes live here: the ring's geometry, taken from the dial on the landing page
(overrides/home.html: a 440-unit box, 19 phase dots on a ring of radius 176 with the first at the
top, 76 ticks with the long ones on the dots). The colours are read from docs/stylesheets/nf.css:
the :root tokens (dark) and the prefers-color-scheme: light tokens. Images carry no version number
and no URL, so a release never needs new ones.

  file                         made by    used by
  neuroflow-mark.svg           --write    mkdocs theme.logo; the vector master (follows light/dark)
  favicon.svg                  --write    mkdocs theme.favicon: docs pages and the landing page
  favicon-32.png               --png      PNG fallback icon (overrides/partials/nf-head.html)
  apple-touch-icon.png         --png      home-screen icon, 180x180, opaque
  icon-512.png                 --png      plugin.json "icon" (plugin directory listing), opaque
  neuroflow-lockup-dark.png    --png      ring and wordmark, light ink, for dark backgrounds (README)
  neuroflow-lockup-light.png   --png      ring and wordmark, dark ink, for light backgrounds (README)
  social-card.png              --png      og:image of every page; GitHub social preview (uploaded by hand)

Usage:
    python scripts/automation/brand_assets.py               # --check (default)
    python scripts/automation/brand_assets.py --write       # write the SVGs
    python scripts/automation/brand_assets.py --png         # render the PNGs
    python scripts/automation/brand_assets.py --png --browser "C:/path/to/chrome.exe"

--check compares the committed SVGs with this generator's output and checks every file in the
folder: PNG sizes, the SVG rules (no <text>, no url(http...), no @import, no external href) and the
weight budget (each file under 512 KB, the folder under 1 MB). It needs no browser and no network.

--png renders the PNGs with headless Chrome or Edge, from HTML pages this script writes to a
temporary folder. It needs the network: the images with text load Albert Sans and DM Mono from
Google Fonts, exactly as the landing page does (no font file is kept in the repo); the icons are
rendered from the same SVG markup. Run --check afterwards and look at every image before committing.

Exit codes: 0 = clean (or written), 1 = drift or a broken rule, 2 = usage or runtime error.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND_DIR = "docs/assets/brand"
NF_CSS = "docs/stylesheets/nf.css"

# ── Shapes ──────────────────────────────────────────────────────────────────────────────────
PHASES = 19          # phase dots on the ring; the first sits at the top
TICKS = PHASES * 4   # 76 ticks; every fourth (the long one) lines up with a dot
TICK_ALPHA = .18     # ink opacities: on the dark stage they give the landing page's greys
RING_ALPHA = .5
DOT_ALPHA = .53      # the poster's dot tone (#7C7E84 on the dark stage); reads at small sizes

WORDMARK = "neuroflow"   # Albert Sans 200, lowercase, tracked -0.025em, x-height centred on the ring
WORD_WEIGHT = 200
WORD_SIZE = 66           # in the 440 box: 0.15 x the box, as in the intro video's title
WORD_TRACKING = -.025    # em


@dataclass(frozen=True)
class Ring:
    """One drawing of the ring, in a square box with the ring at its centre."""

    box: float = 440
    r: float = 176               # the ring
    ring_w: float = 1.25
    dot_r: float = 4             # phase dots
    top_r: float = 4             # the first phase, drawn in the strong colour
    tick_in: float = 196         # ticks run from tick_in to tick_minor, or to tick_major on a dot
    tick_minor: float = 200
    tick_major: float = 204
    tick_w: float = 1
    ticks: bool = True


DIAL = Ring()  # the landing page's dial: the mark, the lockups and the social card
# The square icons: the same ring drawn heavier, so that it holds from 512 px down to about 48 px.
ICON = Ring(box=512, r=172, ring_w=5, dot_r=10, top_r=16,
            tick_in=200, tick_minor=207, tick_major=216, tick_w=3)
TILE_RADIUS = 14 / 64  # favicon corner radius, as a share of the tile

FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link href="https://fonts.googleapis.com/css2?family=Albert+Sans:wght@200..600&amp;family=DM+Mono:'
             'wght@300;400;500&amp;display=swap" rel="stylesheet">')

# ── The asset table ─────────────────────────────────────────────────────────────────────────
SVGS = ("neuroflow-mark.svg", "favicon.svg")
PNGS = {  # name: (width, height) in pixels
    "favicon-32.png": (32, 32),
    "apple-touch-icon.png": (180, 180),
    "icon-512.png": (512, 512),
    "neuroflow-lockup-dark.png": (880, 880),
    "neuroflow-lockup-light.png": (880, 880),
    "social-card.png": (1280, 640),
}
MAX_FILE = 512 * 1024
MAX_TOTAL = 1024 * 1024
SVG_FORBIDDEN = (
    (re.compile(r"<text\b", re.I), "a <text> element (the viewer's fallback font would draw it)"),
    (re.compile(r"url\(\s*['\"]?\s*https?:", re.I), "an external url(...)"),
    (re.compile(r"@import", re.I), "an @import"),
    (re.compile(r"href\s*=\s*['\"]\s*(?:https?:)?//", re.I), "an external href"),
)


class BrandError(Exception):
    """A usage or runtime problem (exit 2)."""


# ── Colours from nf.css ─────────────────────────────────────────────────────────────────────
_DECL = re.compile(r"(--nf-[a-z0-9-]+)\s*:\s*([^;{}]+)")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
NEEDED = {"dark": ("bg", "fg", "strong", "mute", "dim"), "light": ("bg", "fg", "strong")}


def read_tokens(css: str) -> dict[str, dict[str, str]]:
    """The --nf-* tokens of nf.css: 'dark' from the top-level :root, 'light' = dark plus the
    :root inside @media (prefers-color-scheme: light)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found: dict[str, dict[str, str]] = {"dark": {}, "light": {}}
    stack: list[str] = []
    start = 0
    for i, ch in enumerate(css):
        if ch == "{":
            stack.append(" ".join(css[start:i].split(";")[-1].split()))
            start = i + 1
        elif ch == "}":
            if stack and stack[-1] == ":root":
                outer = [s.replace(" ", "") for s in stack[:-1]]
                scheme = "dark" if not outer else "light" if outer == ["@media(prefers-color-scheme:light)"] else ""
                if scheme:
                    for name, value in _DECL.findall(css[start:i]):
                        found[scheme][name[len("--nf-"):]] = value.strip()
            if stack:
                stack.pop()
            start = i + 1
    found["light"] = {**found["dark"], **found["light"]}
    return found


def palette(root: Path) -> dict[str, dict[str, str]]:
    path = root / NF_CSS
    try:
        tokens = read_tokens(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BrandError(f"cannot read {NF_CSS}: {exc}") from exc
    for scheme, names in NEEDED.items():
        for name in names:
            value = tokens[scheme].get(name, "")
            if not _HEX.match(value):
                raise BrandError(f"{NF_CSS}: --nf-{name} ({scheme}) must be a #RRGGBB colour, "
                                 f"found {value or 'nothing'!r}")
    return tokens


# ── SVG building blocks ─────────────────────────────────────────────────────────────────────
def num(value: float, digits: int = 1) -> str:
    """A coordinate with at most `digits` decimals and no trailing zeros (deterministic output)."""
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def alpha(value: float) -> str:
    return f"{value:g}".lstrip("0") or "0"


def at(ring: Ring, radius: float, turn: float, dy: float = 0) -> tuple[float, float]:
    """A point on a circle around the box centre, `turn` (0..1) of the way round clockwise from 12 o'clock."""
    angle = 2 * math.pi * turn
    centre = ring.box / 2
    return centre + radius * math.sin(angle), centre + dy - radius * math.cos(angle)


def ring_arcs(ring: Ring, dy: float = 0) -> str:
    """The ring as 19 arcs that stop at the dots: a see-through dot never doubles up with the ring."""
    gap = [ring.top_r] + [ring.dot_r] * (PHASES - 1)   # half the gap, as arc length, at each dot
    turn = 2 * math.pi * ring.r
    arcs = []
    for k in range(PHASES):
        x0, y0 = at(ring, ring.r, k / PHASES + gap[k] / turn, dy)
        x1, y1 = at(ring, ring.r, (k + 1) / PHASES - gap[(k + 1) % PHASES] / turn, dy)
        arcs.append(f"M{num(x0, 2)} {num(y0, 2)}A{num(ring.r)} {num(ring.r)} 0 0 1 {num(x1, 2)} {num(y1, 2)}")
    return "".join(arcs)


def ring_parts(ring: Ring, ink: str, strong: str, dy: float = 0, classes: bool = False) -> list[str]:
    """Ticks, the ring, 18 phase dots and the first one. With classes=True the elements also carry
    classes (t, r, d, s) for a stylesheet to recolour them; their attributes stay the fallback."""
    cls = (lambda name: f' class="{name}"') if classes else (lambda name: "")
    parts = []
    if ring.ticks:
        path = []
        for j in range(TICKS):
            x0, y0 = at(ring, ring.tick_in, j / TICKS, dy)
            x1, y1 = at(ring, ring.tick_major if j % 4 == 0 else ring.tick_minor, j / TICKS, dy)
            path.append(f"M{num(x0)} {num(y0)}L{num(x1)} {num(y1)}")
        parts.append(f'<path{cls("t")} d="{"".join(path)}" fill="none" stroke="{ink}" '
                     f'stroke-opacity="{alpha(TICK_ALPHA)}" stroke-width="{num(ring.tick_w)}"/>')
    parts.append(f'<path{cls("r")} d="{ring_arcs(ring, dy)}" fill="none" stroke="{ink}" '
                 f'stroke-opacity="{alpha(RING_ALPHA)}" stroke-width="{num(ring.ring_w, 2)}"/>')
    dots = "".join(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(ring.dot_r)}"/>'
                   for x, y in (at(ring, ring.r, k / PHASES, dy) for k in range(1, PHASES)))
    parts.append(f'<g{cls("d")} fill="{ink}" fill-opacity="{alpha(DOT_ALPHA)}">{dots}</g>')
    x, y = at(ring, ring.r, 0, dy)
    parts.append(f'<circle{cls("s")} cx="{num(x)}" cy="{num(y)}" r="{num(ring.top_r)}" fill="{strong}"/>')
    return parts


def mark_svg(colors: dict[str, dict[str, str]]) -> str:
    """The ring alone on a clear background; a light colour scheme switches it to dark ink."""
    dark, light = colors["dark"], colors["light"]
    style = (f"@media (prefers-color-scheme: light){{.t,.r{{stroke:{light['fg']}}}"
             f".d{{fill:{light['fg']}}}.s{{fill:{light['strong']}}}}}")
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 440" width="440" height="440" '
             'role="img" aria-label="neuroflow">', f"<style>{style}</style>",
             *ring_parts(DIAL, dark["fg"], dark["strong"], classes=True), "</svg>"]
    return "\n".join(lines) + "\n"


def favicon_body(colors: dict[str, dict[str, str]]) -> list[str]:
    """The ring reduced for 16-32 px: a tile, a heavy ring and the bright first dot."""
    dark = colors["dark"]
    return [f'<rect width="64" height="64" rx="{num(64 * TILE_RADIUS)}" fill="{dark["bg"]}"/>',
            f'<circle cx="32" cy="33" r="19" fill="none" stroke="{dark["fg"]}" stroke-opacity=".6" stroke-width="4"/>',
            f'<circle cx="32" cy="14" r="6" fill="{dark["strong"]}"/>']


def favicon_svg(colors: dict[str, dict[str, str]]) -> str:
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">',
             *favicon_body(colors), "</svg>"]
    return "\n".join(lines) + "\n"


def icon_svg(colors: dict[str, dict[str, str]], size: int) -> str:
    """The opaque square icon (no rounded corners: the platform masks it): the ring, drawn heavier."""
    dark = colors["dark"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(ICON.box)} {num(ICON.box)}" '
            f'width="{size}" height="{size}">'
            f'<rect width="{num(ICON.box)}" height="{num(ICON.box)}" fill="{dark["bg"]}"/>'
            + "".join(ring_parts(ICON, dark["fg"], dark["strong"], dy=ICON.top_r / 3)) + "</svg>")


SVG_MAKERS = {"neuroflow-mark.svg": mark_svg, "favicon.svg": favicon_svg}


# ── HTML pages for the PNGs ─────────────────────────────────────────────────────────────────
READY = """<script>
(async () => {
  // Marks the page ready once every face it uses has loaded; the wordmark's x-height is then
  // centred on the ring's centre.
  const faces = %s;
  let ok = true;
  try {
    const sets = await Promise.all(faces.map(([font, text]) => document.fonts.load(font, text)));
    ok = sets.every((list) => list.length > 0 && list.every((face) => face.status === 'loaded'));
  } catch (error) {
    ok = false;
  }
  if (ok) {
    const ctx = document.createElement('canvas').getContext('2d');
    document.querySelectorAll('[data-cy]').forEach((word) => {
      ctx.font = word.getAttribute('data-font');
      const xHeight = ctx.measureText('x').actualBoundingBoxAscent;
      word.setAttribute('y', (Number(word.getAttribute('data-cy')) + xHeight / 2).toFixed(2));
    });
  }
  document.documentElement.setAttribute('data-nf', ok ? 'ready' : 'fonts-missing');
})();
</script>"""


WORD_FACE = (f'{WORD_WEIGHT} {WORD_SIZE}px "Albert Sans"', WORDMARK)  # (CSS font, text) to load


def wordmark(color: str, centre: float = 220) -> str:
    """The wordmark as SVG text in the rendering page only (the browser draws it in Albert Sans);
    the page script moves it down so that its x-height is centred on `centre`."""
    return (f'<text data-cy="{num(centre)}" data-font=\'{WORD_FACE[0]}\' x="{num(centre)}" y="{num(centre)}" '
            f'text-anchor="middle" font-family="Albert Sans" font-weight="{WORD_WEIGHT}" '
            f'font-size="{WORD_SIZE}" letter-spacing="{WORD_SIZE * WORD_TRACKING:g}" fill="{color}">{WORDMARK}</text>')


def lockup_svg(scheme: dict[str, str], word_color: str) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 440" width="440" height="440">'
            + "".join(ring_parts(DIAL, scheme["fg"], scheme["strong"])) + wordmark(word_color) + "</svg>")


def page(body: str, css: str = "", faces: list[tuple[str, str]] | None = None) -> str:
    """A page for one screenshot: the fonts link when it has text, and the script that marks it ready."""
    head = FONT_LINK if faces else ""
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n" + head
            + f"\n<style>html,body{{margin:0;background:transparent}}svg{{display:block}}{css}</style>\n"
            + f"</head>\n<body>\n{body}\n" + READY % json.dumps(faces or []) + "\n</body>\n</html>\n")


def lockup_page(colors: dict[str, dict[str, str]], scheme: str) -> str:
    tokens = colors[scheme]
    word = tokens["strong"] if scheme == "dark" else tokens["fg"]
    return page(lockup_svg(tokens, word), faces=[WORD_FACE])


def rgba(hex_colour: str, opacity: float) -> str:
    return "rgba({},{},{},{})".format(*(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)), alpha(opacity))


def social_page(colors: dict[str, dict[str, str]]) -> str:
    """1280x640, dark: the pitch on the left, the lockup on the right under the landing page's glow,
    nothing within 72 px of an edge."""
    dark = colors["dark"]
    css = (".card{position:relative;width:1280px;height:640px;overflow:hidden;background:radial-gradient("
           f"circle at 980px 320px,{rgba(dark['fg'], .045)},{rgba(dark['bg'], 0)} 36%),{dark['bg']}}}"
           ".copy{position:absolute;left:80px;top:50%;width:640px;transform:translateY(-50%);"
           "display:flex;flex-direction:column;gap:28px}"
           ".label{font-family:'DM Mono',monospace;font-size:16px;font-weight:400;letter-spacing:.2em;"
           f"color:{dark['dim']}}}"
           "h1{margin:0;font-family:'Albert Sans',sans-serif;font-size:52px;line-height:1.1;font-weight:200;"
           f"letter-spacing:-.035em;color:{dark['fg']}}}"
           "p{margin:0;font-family:'Albert Sans',sans-serif;font-size:24px;line-height:1.45;font-weight:300;"
           f"color:{dark['mute']}}}"
           ".lockup{position:absolute;left:760px;top:100px}")
    body = ('<div class="card">\n<div class="copy">\n'
            '<div class="label">CLAUDE CODE PLUGIN &#183; OPEN SOURCE</div>\n'
            '<h1>Your team&#8217;s shared memory.<br>Inside Claude Code.</h1>\n'
            '<p>A complete research system for neuroscience teams.</p>\n</div>\n'
            f'<div class="lockup">{lockup_svg(dark, dark["strong"])}</div>\n</div>')
    faces = [WORD_FACE, ("200 52px \"Albert Sans\"", "Your team’s shared memory. Inside Claude Code."),
             ("300 24px \"Albert Sans\"", "A complete research system for neuroscience teams."),
             ("400 16px \"DM Mono\"", "CLAUDE CODE PLUGIN · OPEN SOURCE")]
    return page(body, css, faces)


def favicon_png_svg(colors: dict[str, dict[str, str]]) -> str:
    """favicon.svg's drawing at 32 px, for the PNG fallback."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="32" height="32">'
            + "".join(favicon_body(colors)) + "</svg>")


def raster_pages(colors: dict[str, dict[str, str]]) -> dict[str, tuple[str, int]]:
    """name: (HTML page, device pixels per CSS pixel); the window is the PNG size over the scale."""
    return {
        "favicon-32.png": (page(favicon_png_svg(colors)), 1),
        "apple-touch-icon.png": (page(icon_svg(colors, 180)), 1),
        "icon-512.png": (page(icon_svg(colors, 512)), 1),
        "neuroflow-lockup-dark.png": (lockup_page(colors, "dark"), 2),
        "neuroflow-lockup-light.png": (lockup_page(colors, "light"), 2),
        "social-card.png": (social_page(colors), 1),
    }


# ── Rendering ───────────────────────────────────────────────────────────────────────────────
def find_browser(given: str | None) -> str:
    if given:
        path = shutil.which(given) or (given if Path(given).is_file() else None)
        if not path:
            raise BrandError(f"--browser {given}: no such program")
        return path
    candidates = []
    for env, rel in (("PROGRAMFILES", r"Google\Chrome\Application\chrome.exe"),
                     ("PROGRAMFILES(X86)", r"Google\Chrome\Application\chrome.exe"),
                     ("LOCALAPPDATA", r"Google\Chrome\Application\chrome.exe"),
                     ("PROGRAMFILES(X86)", r"Microsoft\Edge\Application\msedge.exe"),
                     ("PROGRAMFILES", r"Microsoft\Edge\Application\msedge.exe")):
        if os.environ.get(env):
            candidates.append(str(Path(os.environ[env]) / rel))
    candidates += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Chromium.app/Contents/MacOS/Chromium",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for path in candidates:
        if Path(path).is_file():
            return path
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
                 "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    raise BrandError("no Chrome, Chromium or Edge found; pass --browser PATH")


def render(browser: str, html: str, out: Path, size: tuple[int, int], scale: int, work: Path) -> None:
    """Screenshot one page with headless Chrome or Edge, after its fonts have loaded."""
    width, height = size
    if width % scale or height % scale:
        raise BrandError(f"{out.name}: {width}x{height} is not a multiple of the scale {scale}")
    source = work / (out.stem + ".html")
    source.write_bytes(html.encode("utf-8"))
    shot = work / out.name
    profile = work / ("profile-" + out.stem)
    args = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", f"--user-data-dir={profile}",
            "--force-color-profile=srgb", "--disable-lcd-text", f"--force-device-scale-factor={scale}",
            "--default-background-color=00000000", "--virtual-time-budget=20000",
            f"--window-size={width // scale},{height // scale}", f"--screenshot={shot}", "--dump-dom",
            source.as_uri()]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrandError(f"{out.name}: the browser did not run: {exc}") from exc
    if not shot.is_file():
        tail = " | ".join((proc.stderr or "").strip().splitlines()[-3:])
        raise BrandError(f"{out.name}: the browser wrote no screenshot (exit {proc.returncode}): {tail}")
    if 'data-nf="fonts-missing"' in proc.stdout:
        raise BrandError(f"{out.name}: the fonts did not load from Google Fonts (is the network up?)")
    if 'data-nf="ready"' not in proc.stdout:
        raise BrandError(f"{out.name}: the page did not finish (no ready mark in its DOM)")
    data = shot.read_bytes()
    if png_size(data) != size:
        raise BrandError(f"{out.name}: the browser wrote {png_size(data)}, expected {size}")
    out.write_bytes(data)


def render_all(root: Path, colors: dict[str, dict[str, str]], browser: str) -> list[str]:
    folder = root / BRAND_DIR
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    # A browser may hold its profile files for a moment after it exits (Windows): cleanup may fail.
    with tempfile.TemporaryDirectory(prefix="nf-brand-", ignore_cleanup_errors=True) as tmp:
        for name, (html, scale) in raster_pages(colors).items():
            render(browser, html, folder / name, PNGS[name], scale, Path(tmp))
            written.append(name)
    return written


# ── Checks ──────────────────────────────────────────────────────────────────────────────────
def png_size(data: bytes) -> tuple[int, int] | None:
    """(width, height) from the IHDR chunk, or None when the bytes are not a PNG."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def svg_problems(text: str) -> list[str]:
    return [what for pattern, what in SVG_FORBIDDEN if pattern.search(text)]


def same_svg(path: Path, data: bytes) -> bool:
    """The committed SVG equals the generator's output (a checkout may have turned LF into CRLF)."""
    return path.is_file() and path.read_bytes().replace(b"\r\n", b"\n") == data


def write_svgs(root: Path, colors: dict[str, dict[str, str]]) -> list[str]:
    folder = root / BRAND_DIR
    folder.mkdir(parents=True, exist_ok=True)
    changed = []
    for name in SVGS:
        data = SVG_MAKERS[name](colors).encode("utf-8")
        path = folder / name
        if not same_svg(path, data):
            path.write_bytes(data)
            changed.append(name)
    return changed


def check(root: Path, colors: dict[str, dict[str, str]]) -> list[str]:
    folder = root / BRAND_DIR
    findings = []
    for name in SVGS:
        path = folder / name
        if not path.is_file():
            findings.append(f"{name}: missing (run --write)")
        elif not same_svg(path, SVG_MAKERS[name](colors).encode("utf-8")):
            findings.append(f"{name}: differs from the generator's output (run --write, or change the generator)")
    for name, size in PNGS.items():
        path = folder / name
        if not path.is_file():
            findings.append(f"{name}: missing (run --png)")
            continue
        got = png_size(path.read_bytes())
        if got is None:
            findings.append(f"{name}: not a PNG file")
        elif got != size:
            findings.append(f"{name}: {got[0]}x{got[1]}, expected {size[0]}x{size[1]} (run --png)")
    total = 0
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    for path in files:
        size = path.stat().st_size
        total += size
        if path.name not in SVGS and path.name not in PNGS:
            findings.append(f"{path.name}: not made by this generator (add it to the asset table or remove it)")
        if size > MAX_FILE:
            findings.append(f"{path.name}: {size // 1024} KB, over the {MAX_FILE // 1024} KB limit for one image")
        if path.suffix.lower() == ".svg":
            for what in svg_problems(path.read_text(encoding="utf-8", errors="replace")):
                findings.append(f"{path.name}: contains {what}")
    if total > MAX_TOTAL:
        findings.append(f"{BRAND_DIR}: {total // 1024} KB in all, over the {MAX_TOTAL // 1024} KB limit")
    return findings


# ── Command line ────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Write, render and check the neuroflow ring images in docs/assets/brand/.",
        epilog="--png needs the network: the images with text load Albert Sans and DM Mono from Google Fonts, "
               "as the landing page does. Exit codes: 0 clean or written, 1 drift or a broken rule, 2 error.")
    ap.add_argument("--check", action="store_true", help="compare the SVGs with the generator and check every "
                    "image: sizes, SVG rules, weight (the default; needs no browser)")
    ap.add_argument("--write", action="store_true", help="write the SVGs (neuroflow-mark.svg, favicon.svg)")
    ap.add_argument("--png", action="store_true", help="render the PNGs with headless Chrome or Edge (needs the network)")
    ap.add_argument("--browser", metavar="PATH", help="the Chrome, Chromium or Edge program to render with")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.browser and not args.png:
        ap.error("--browser goes with --png")
    for stream in (sys.stdout, sys.stderr):  # messages quote paths; a local console may not encode them
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    root = args.root.resolve()
    mode = "png" if args.png else "write" if args.write else "check"
    result: dict = {"tool": "brand_assets", "mode": mode, "written": [], "rendered": [], "findings": []}
    try:
        colors = palette(root)
        if args.write:
            result["written"] = write_svgs(root, colors)
        if args.png:
            result["rendered"] = render_all(root, colors, find_browser(args.browser))
        if args.check or not (args.write or args.png):
            result["findings"] = check(root, colors)
    except BrandError as exc:
        result.update(error=str(exc), exit_code=2)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"brand_assets: {exc}", file=sys.stderr)
        return 2
    code = 1 if result["findings"] else 0
    result["exit_code"] = code
    if args.json:
        print(json.dumps(result, indent=2))
        return code
    for name in result["written"]:
        print(f"wrote {BRAND_DIR}/{name}")
    if args.write and not result["written"]:
        print("brand_assets: the SVGs are up to date")
    for name in result["rendered"]:
        print(f"rendered {BRAND_DIR}/{name}")
    for line in result["findings"]:
        print(f"FAIL {line}")
    if mode == "check" or args.check:
        if not result["findings"]:
            print(f"brand_assets: OK - {len(SVGS)} SVGs match the generator, {len(PNGS)} PNGs have their sizes")
    return code


if __name__ == "__main__":
    sys.exit(main())
