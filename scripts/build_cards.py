"""Draw the profile README cards as SVG files in assets/.

Run from the repo root:  python scripts/build_cards.py
Needs: pip install fonttools brotli

Style: chunky cartoon cards. Navy dotted ground, saturated colour blocks, ink outlines
and hard offset shadows. Fonts (Baloo 2, JetBrains Mono) are subset to the characters
each card uses and embedded, so the cards look the same everywhere.
"""
import base64
import io
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"

NAVY, PANEL, INK = "#1b1e30", "#252a42", "#0b0d17"
CREAM, MUTED = "#f8f2e4", "#aab0cf"
COLORS = {
    "blue": "#2f5fb4", "green": "#2e7d50", "orange": "#cc6a2c",
    "purple": "#6a49ad", "red": "#b53a55", "teal": "#1f7778",
}
SHADOW = 6  # hard offset shadow, px

FACES = {  # family name used in the SVG -> (file, weight)
    "Display800": ("baloo-2-latin.woff2", 800),
    "Display700": ("baloo-2-latin.woff2", 700),
    "Display500": ("baloo-2-latin.woff2", 500),
    "Mono": ("jetbrains-mono-latin.woff2", 500),
}
_fonts = {}


def font(face):
    if face not in _fonts:
        file, weight = FACES[face]
        _fonts[face] = instancer.instantiateVariableFont(TTFont(FONTS / file), {"wght": weight})
    return _fonts[face]


def width(text, face, size):
    f = font(face)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text) * size / upm


def wrap(text, face, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, face, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


class Card:
    """Collects SVG elements plus the text used per font face (for subsetting)."""

    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.parts, self.used = w, h, title, [], {}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, face, size, fill=CREAM, anchor="start", extra=""):
        self.used[face] = self.used.get(face, "") + s
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{face}" font-size="{size}" '
                 f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')
        return width(s, face, size)

    def block(self, x, y, w, h, fill, r=20, shadow=SHADOW, border=2.5, dots=False):
        """Rounded block with an ink outline and a hard offset shadow."""
        self.add(f'<rect x="{x + shadow}" y="{y + shadow}" width="{w}" height="{h}" rx="{r}" fill="{INK}"/>')
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
                 f'stroke="{INK}" stroke-width="{border}"/>')
        if dots:
            self.add(f'<rect x="{x + 2}" y="{y + 2}" width="{w - 4}" height="{h - 4}" rx="{r - 2}" fill="url(#dots)"/>')

    def chip(self, x, y, label, color, size=16, h=34, pad=14, face="Display700", fg=CREAM, shadow=3):
        w = width(label, face, size) + 2 * pad
        self.block(x, y, w, h, color, r=10, shadow=shadow, border=2)
        self.text(x + pad, y + h / 2 + size * 0.36, label, face, size, fg)
        return w

    def svg(self):
        faces = []
        for face, chars in self.used.items():
            buf = io.BytesIO()
            font(face).save(buf)
            buf.seek(0)
            g = TTFont(buf)  # subset a copy so later cards keep every glyph
            opts = subset.Options()
            opts.layout_features = ["kern", "liga"]
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(set(chars))))
            sub.subset(g)
            g.flavor = "woff2"
            out = io.BytesIO()
            g.save(out)
            data = base64.b64encode(out.getvalue()).decode()
            faces.append(f'@font-face{{font-family:{face};src:url(data:font/woff2;base64,{data}) format("woff2")}}')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
                f'<title>{escape(self.title)}</title><defs><style>{"".join(faces)}</style>'
                '<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">'
                '<circle cx="2" cy="2" r="1.3" fill="#ffffff" fill-opacity="0.07"/></pattern></defs>'
                + "".join(self.parts) + "</svg>")


def save(name, card):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(card.svg(), encoding="utf-8")
    print(f"assets/{name}  {card.w}x{card.h}")


# ---------------------------------------------------------------- hero
def hero():
    W, H = 840, 330
    c = Card(W, H, "Hi, I'm Salah. Data Science and AI engineering student in Sousse, Tunisia, "
                   "building ML pipelines, data warehouses and the apps around them. Machine "
                   "learning, data engineering, backend and APIs, Flutter apps. Open to a PFE "
                   "(final-year) internship.")
    c.block(0, 0, W - SHADOW, H - SHADOW, NAVY, r=26, dots=True)
    # monogram: cream tile with an orange offset block behind it
    c.add('<g transform="rotate(-5 100 112)">')
    c.add(f'<rect x="58" y="72" width="96" height="96" rx="22" fill="{COLORS["orange"]}" '
          f'stroke="{INK}" stroke-width="3" transform="translate(9 9)"/>')
    c.add(f'<rect x="58" y="72" width="96" height="96" rx="22" fill="{CREAM}" stroke="{INK}" stroke-width="4"/>')
    c.text(106, 145, "S", "Display800", 78, INK, "middle")
    c.add("</g>")
    # greeting, with the name on a red block
    x, y = 190, 128
    w = c.text(x, y, "Hi, I'm", "Display800", 66)
    nx = x + w + 14
    nw = width("Salah", "Display800", 66) + 28
    c.block(nx, y - 62, nw, 80, COLORS["red"], r=16, shadow=5, border=3)
    c.text(nx + 14, y, "Salah", "Display800", 66)
    c.text(x, y + 44, "Data Science & AI engineering student in Sousse, Tunisia,", "Display500", 21, CREAM)
    c.text(x, y + 70, "building ML pipelines, data warehouses and the apps around them.", "Display500", 21, CREAM)
    cx = x
    for label, col in [("Machine learning", "blue"), ("Data engineering", "orange"),
                       ("Backend & APIs", "purple"), ("Flutter apps", "green")]:
        cx += c.chip(cx, y + 94, label, COLORS[col]) + 12
    assert cx <= W - 30, "hero chips overflow"
    # status line
    c.add(f'<circle cx="{x + 8}" cy="{y + 166}" r="6" fill="#5fd38a" stroke="{INK}" stroke-width="2"/>')
    c.text(x + 24, y + 171, "open to a PFE (final-year) internship", "Mono", 15, MUTED)
    # tilted sticker, top right
    label = "salahghezaiel.me"
    sw = width(label, "Display800", 20) + 34
    sx = W - SHADOW - 36 - sw
    c.add(f'<g transform="rotate(6 {sx + sw / 2} 52)">')
    c.block(sx, 30, sw, 44, COLORS["orange"], r=12, shadow=5, border=3)
    c.text(sx + sw / 2, 60, label, "Display800", 20, INK, "middle")
    c.add("</g>")
    return c


# ---------------------------------------------------------------- link buttons
ICONS = {
    "globe": '<circle cx="10" cy="10" r="9"/><path d="M1 10h18M10 1c3 3 3 15 0 18M10 1c-3 3-3 15 0 18"/>',
    "in": '<rect x="1" y="1" width="18" height="18" rx="4"/><path d="M6 8.5v6M6 5.5v.2M10 14.5v-6M10 11c0-2 4-3 4 0v3.5"/>',
    "mail": '<rect x="1" y="3" width="18" height="14" rx="3"/><path d="m2 5 8 6 8-6"/>',
    "doc": '<path d="M4 1h8l5 5v13H4z"/><path d="M12 1v5h5M7 11h7M7 15h7"/>',
}


def button(label, color, icon):
    w = int(width(label, "Display700", 19) + 72)
    c = Card(w + 5, 56, label)
    c.block(0, 0, w, 50, COLORS[color], r=14, shadow=5, border=2.5)
    c.add(f'<g transform="translate(19 15)" fill="none" stroke="{CREAM}" stroke-width="2.2" '
          f'stroke-linecap="round" stroke-linejoin="round">{icon}</g>')
    c.text(50, 32, label, "Display700", 19)
    return c


# ---------------------------------------------------------------- section header
def header(title, note):
    W, H = 840, 76
    c = Card(W, H, title)
    c.block(0, 0, W - SHADOW, H - SHADOW, NAVY, r=20, dots=True)
    c.text(30, 47, title, "Display800", 32)
    c.text(W - SHADOW - 30, 44, note, "Mono", 14, MUTED, "end")
    return c


# ---------------------------------------------------------------- project tiles
PROJECT_ICONS = {  # 28x28, drawn in cream strokes
    "spark": '<path d="M14 2c1 6 4 9 12 12-8 3-11 6-12 12-1-6-4-9-12-12 8-3 11-6 12-12z"/>',
    "db": '<ellipse cx="14" cy="6" rx="11" ry="4"/><path d="M3 6v16c0 2.2 4.9 4 11 4s11-1.8 11-4V6M3 14c0 2.2 4.9 4 11 4s11-1.8 11-4"/>',
    "nodes": '<circle cx="6" cy="6" r="4"/><circle cx="22" cy="6" r="4"/><circle cx="14" cy="22" r="4"/><path d="M10 6h8M8 9.5l4 9M20 9.5l-4 9"/>',
    "ball": '<circle cx="14" cy="14" r="12"/><path d="M14 8l5 3.6-2 6H11l-2-6z"/><path d="M14 2v6M24.5 9.5l-5.5 2M21 23l-4-5M7 23l4-5M3.5 9.5l5.5 2"/>',
}


def project(kicker, color, icon, title, desc, stack):
    W, H = 410, 286
    c = Card(W, H, f"{title}: {desc} Stack: {', '.join(stack)}.")
    c.block(0, 0, W - SHADOW, H - SHADOW, COLORS[color], r=22, dots=True)
    # icon badge, top right
    c.block(W - SHADOW - 64, 20, 46, 46, CREAM, r=12, shadow=3, border=2.5)
    c.add(f'<g transform="translate({W - SHADOW - 64 + 9} 29)" fill="none" stroke="{INK}" stroke-width="2.2" '
          f'stroke-linecap="round" stroke-linejoin="round">{PROJECT_ICONS[icon]}</g>')
    c.text(26, 44, kicker.upper(), "Mono", 13, CREAM, extra='fill-opacity="0.8" letter-spacing="1"')
    y = 92
    for line in wrap(title, "Display800", 29, 352):
        c.text(26, y, line, "Display800", 29)
        y += 32
    y += 4
    for line in wrap(desc, "Display500", 16, 352):
        c.text(26, y, line, "Display500", 16, CREAM, extra='fill-opacity="0.92"')
        y += 21
    cy = H - SHADOW - 24 - 30
    assert (y - 21) + 6 <= cy - 8, f"text overflows on {title}"
    x = 26
    for s in stack:
        w = width(s, "Mono", 13) + 20
        c.add(f'<rect x="{x}" y="{cy}" width="{w:.1f}" height="30" rx="8" fill="{INK}" fill-opacity="0.35"/>')
        c.text(x + 10, cy + 20, s, "Mono", 13)
        x += w + 8
    assert x <= W - SHADOW - 16, f"stack chips overflow on {title}"
    return c


# ---------------------------------------------------------------- tech stack
STACK = [
    ("languages", "blue", ["Python", "Java", "C", "C++", "SQL", "Dart"]),
    ("ml & data", "green", ["pandas", "scikit-learn", "XGBoost", "Matplotlib", "Seaborn"]),
    ("backend", "purple", ["Node.js", "Express", "REST", "GraphQL", "gRPC", "Kafka"]),
    ("databases", "orange", ["PostgreSQL", "MySQL", "MongoDB", "Firebase"]),
    ("apps & web", "red", ["Flutter", "Angular", "Django", "Symfony", ".NET"]),
    ("tools", "teal", ["Git", "GitHub", "Robot Framework"]),
]


def stack_card():
    W = 840
    H = 104 + len(STACK) * 50 + 16 + SHADOW
    c = Card(W, H, "Tech stack. " + " ".join(
        f"{label}: {', '.join(items)}." for label, _, items in STACK))
    c.block(0, 0, W - SHADOW, H - SHADOW, NAVY, r=26, dots=True)
    c.text(32, 62, "Tech stack", "Display800", 34)
    c.text(W - SHADOW - 32, 58, "what I build with", "Mono", 14, MUTED, "end")
    y = 92
    for label, col, items in STACK:
        c.text(32, y + 23, label, "Mono", 14, MUTED)
        x = 172
        for it in items:
            x += c.chip(x, y, it, COLORS[col], size=16, h=34, pad=13) + 11
        assert x <= W - SHADOW - 20, f"stack row overflows: {label}"
        y += 50
    return c


if __name__ == "__main__":
    save("hero.svg", hero())
    for name, label, col, icon in [("btn-portfolio.svg", "Portfolio", "orange", "globe"),
                                   ("btn-linkedin.svg", "LinkedIn", "blue", "in"),
                                   ("btn-email.svg", "Email", "green", "mail"),
                                   ("btn-resume.svg", "Resume", "purple", "doc")]:
        save(name, button(label, col, ICONS[icon]))
    save("header-work.svg", header("Featured work", "click a card to open the repo"))
    save("project-fashion.svg", project(
        "Machine learning", "blue", "spark", "Fashion Recommendation System",
        "Hybrid recommender on the H&M dataset: SVD collaborative filtering blended with "
        "content similarity, served by a Flask API.",
        ["Python", "scikit-learn", "Flask"]))
    save("project-warehouse.svg", project(
        "Data engineering", "orange", "db", "E-Commerce Data Warehouse",
        "PostgreSQL star schema (a sales fact table and five dimensions) on the Olist "
        "dataset, loaded by a Python ETL pipeline.",
        ["PostgreSQL", "Python", "pygrametl"]))
    save("project-stadium.svg", project(
        "Backend", "purple", "nodes", "Stadium Reservation Microservices",
        "Node.js microservices behind a REST + GraphQL gateway, talking over gRPC and "
        "publishing events on Kafka.",
        ["Node.js", "gRPC", "Kafka"]))
    save("project-injury.svg", project(
        "ML · sports data", "green", "ball", "Soccer Player Injury Prediction",
        "Ranks next-season injury risk from earlier-season data, split by player. "
        "ROC-AUC 0.69 vs 0.50 for chance.",
        ["Python", "XGBoost", "pandas"]))
    save("stack.svg", stack_card())
