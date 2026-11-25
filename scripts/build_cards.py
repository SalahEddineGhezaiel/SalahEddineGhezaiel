"""Draw the profile README cards as SVG files in assets/.

Run from the repo root:  python scripts/build_cards.py
Needs: pip install fonttools brotli

Fonts are subset to the characters each card uses and embedded as base64,
so the cards render the same everywhere GitHub shows them.
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

# Palette: the portfolio's dark theme (salahghezaiel.me)
BG, SURFACE, LINE = "#262624", "#30302e", "#3e3e3a"
TEXT, MUTED, CLAY = "#f5f4ee", "#b7b5a9", "#d97757"
TINTS = {  # chip colour: (fill, text)
    "clay": ("#4a3129", "#f0a589"),
    "sage": ("#2f3d2e", "#a9cf9f"),
    "blue": ("#2c3646", "#a9c1e8"),
    "amber": ("#433a28", "#e3c27f"),
    "plum": ("#3b2f40", "#cfb0dc"),
}

FACES = {  # family name in the SVG -> (file, weight)
    "Serif500": ("source-serif-4-latin.woff2", 500),
    "Serif600": ("source-serif-4-latin.woff2", 600),
    "Sans400": ("source-sans-3-latin.woff2", 400),
    "Sans600": ("source-sans-3-latin.woff2", 600),
}
_fonts = {}


def font(face):
    if face not in _fonts:
        file, weight = FACES[face]
        f = TTFont(FONTS / file)
        _fonts[face] = instancer.instantiateVariableFont(f, {"wght": weight})
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
    """Collects SVG elements and the text used per font face (for subsetting)."""

    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.parts, self.used = w, h, title, [], {}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, face, size, fill=TEXT, anchor="start", extra=""):
        self.used[face] = self.used.get(face, "") + s
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{face}" font-size="{size}" '
                 f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')
        return width(s, face, size)

    def chip(self, x, y, label, tint, size=15, h=30, pad=13):
        fill, fg = TINTS[tint]
        w = width(label, "Sans600", size) + 2 * pad
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="9" fill="{fill}"/>')
        self.text(x + pad, y + h / 2 + size * 0.35, label, "Sans600", size, fg)
        return w

    def frame(self, dots=True):
        self.add(f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="22" '
                 f'fill="{BG}" stroke="{LINE}"/>')
        if dots:  # quiet dot grid, the card's only texture
            self.add(f'<rect x="1" y="1" width="{self.w - 2}" height="{self.h - 2}" rx="21" fill="url(#dots)"/>')

    def svg(self):
        faces = []
        for face, chars in self.used.items():
            f = font(face)
            buf = io.BytesIO()
            opts = subset.Options()
            opts.flavor, opts.layout_features = "woff2", ["kern", "liga"]
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(set(chars))))
            g = TTFont()  # subset a copy so later cards still have every glyph
            f.save(buf)
            buf.seek(0)
            g = TTFont(buf)
            sub.subset(g)
            out = io.BytesIO()
            g.flavor = "woff2"
            g.save(out)
            data = base64.b64encode(out.getvalue()).decode()
            faces.append(f'@font-face{{font-family:{face};src:url(data:font/woff2;base64,{data}) format("woff2")}}')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
                f'<title>{escape(self.title)}</title><defs><style>{"".join(faces)}</style>'
                f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                f'<circle cx="2" cy="2" r="1.1" fill="#ffffff" fill-opacity="0.05"/></pattern></defs>'
                + "".join(self.parts) + "</svg>")


def save(name, card):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(card.svg(), encoding="utf-8")
    print(f"assets/{name}  {card.w}x{card.h}")


# ---------------------------------------------------------------- hero
def hero():
    c = Card(840, 300, "Hi, I'm Salah. Data Science and AI engineering student at the Polytechnic "
                       "School of Sousse, Tunisia. Machine learning, data engineering, backend and "
                       "APIs, Flutter apps. Open to a PFE (final-year) internship.")
    c.frame()
    # monogram tile, slightly tilted, with a soft offset shadow
    c.add('<g transform="rotate(-4 98 104)">'
          '<rect x="52" y="64" width="92" height="92" rx="20" fill="#000" fill-opacity="0.35" transform="translate(5 7)"/>'
          f'<rect x="52" y="64" width="92" height="92" rx="20" fill="{CLAY}"/>'
          '</g>')
    c.text(98, 130, "S", "Serif600", 64, BG, "middle", 'transform="rotate(-4 98 104)"')
    x = 180
    w = c.text(x, 122, "Hi, I'm ", "Serif500", 60)
    c.text(x + w, 122, "Salah", "Serif500", 60, CLAY)
    c.text(x, 160, "Data Science & AI engineering student at the Polytechnic School", "Sans400", 19, MUTED)
    c.text(x, 185, "of Sousse, Tunisia. I build ML pipelines, data warehouses and apps.", "Sans400", 19, MUTED)
    cx = x
    for label, tint in [("Machine learning", "clay"), ("Data engineering", "sage"),
                        ("Backend & APIs", "blue"), ("Flutter apps", "amber")]:
        cx += c.chip(cx, 208, label, tint) + 10
    # status line
    c.add('<circle cx="187" cy="268" r="5" fill="#8cbf7c"/>'
          '<circle cx="187" cy="268" r="9" fill="#8cbf7c" fill-opacity="0.2"/>')
    c.text(203, 274, "Open to a PFE (final-year) internship", "Sans600", 16, TEXT)
    # tilted sticker, top right
    label = "salahghezaiel.me"
    sw = width(label, "Sans600", 17) + 32
    sx = 840 - 40 - sw
    c.add(f'<g transform="rotate(5 {sx + sw / 2} 54)">'
          f'<rect x="{sx}" y="34" width="{sw}" height="40" rx="10" fill="#000" fill-opacity="0.35" transform="translate(4 5)"/>'
          f'<rect x="{sx}" y="34" width="{sw}" height="40" rx="10" fill="{CLAY}"/>')
    c.text(sx + sw / 2, 60, label, "Sans600", 17, BG, "middle")
    c.add("</g>")
    return c


# ---------------------------------------------------------------- link buttons
def button(label, tint, icon):
    fill, fg = TINTS[tint]
    w = int(width(label, "Sans600", 17) + 66)
    c = Card(w, 48, label)
    c.add(f'<rect x="0.5" y="0.5" width="{w - 1}" height="47" rx="13" fill="{fill}" stroke="{fg}" stroke-opacity="0.25"/>')
    c.add(f'<g transform="translate(18 14)" fill="none" stroke="{fg}" stroke-width="1.8" '
          f'stroke-linecap="round" stroke-linejoin="round">{icon}</g>')
    c.text(46, 30, label, "Sans600", 17, fg)
    return c


ICONS = {
    "globe": '<circle cx="10" cy="10" r="9"/><path d="M1 10h18M10 1c3 3 3 15 0 18M10 1c-3 3-3 15 0 18"/>',
    "in": '<rect x="1" y="1" width="18" height="18" rx="4"/><path d="M6 8.5v6M6 5.5v.2M10 14.5v-6M10 11c0-2 4-3 4 0v3.5"/>',
    "mail": '<rect x="1" y="3" width="18" height="14" rx="3"/><path d="m2 5 8 6 8-6"/>',
    "doc": '<path d="M4 1h8l5 5v13H4z"/><path d="M12 1v5h5M7 11h7M7 15h7"/>',
}


# ---------------------------------------------------------------- project cards
def project(kicker, tint, title, desc, stack):
    c = Card(410, 262, f"{title}: {desc} Stack: {', '.join(stack)}.")
    c.frame()
    c.chip(26, 24, kicker, tint, size=13, h=26, pad=10)
    c.add(f'<path d="M372 30l10-10M374 20h8v8" fill="none" stroke="{MUTED}" stroke-width="2" '
          'stroke-linecap="round" stroke-linejoin="round"/>')
    y = 86
    for line in wrap(title, "Serif600", 25, 358):
        c.text(26, y, line, "Serif600", 25)
        y += 31
    y += 2
    for line in wrap(desc, "Sans400", 15.5, 358):
        c.text(26, y, line, "Sans400", 15.5, MUTED)
        y += 21
    x, cy = 26, 262 - 26 - 26
    for s in stack:
        x += c.chip(x, cy, s, tint, size=13, h=26, pad=9) + 7
    assert x <= 410 - 20, f"stack chips overflow on {title}"
    last_baseline = y - 21  # y already points at the next line
    assert last_baseline + 5 <= cy - 10, f"text overflows on {title}"
    return c


# ---------------------------------------------------------------- tech stack
STACK = [
    ("Languages", "clay", ["Python", "Java", "C", "C++", "SQL", "Dart"]),
    ("ML & data", "sage", ["pandas", "scikit-learn", "XGBoost", "Matplotlib", "Seaborn"]),
    ("Backend", "blue", ["Node.js", "Express", "REST", "GraphQL", "gRPC", "Kafka", "Microservices"]),
    ("Databases", "amber", ["PostgreSQL", "MySQL", "MongoDB", "Firebase"]),
    ("Apps & web", "plum", ["Flutter", "Angular", "Django", "Symfony", ".NET"]),
    ("Tools", "clay", ["Git", "GitHub", "Robot Framework"]),
]


def stack_card():
    rows = len(STACK)
    c = Card(840, 96 + rows * 42 + 18, "Tech stack. " + " ".join(
        f"{label}: {', '.join(items)}." for label, _, items in STACK))
    c.frame()
    c.text(34, 58, "Tech stack", "Serif600", 28)
    y = 92
    for label, tint, items in STACK:
        c.text(34, y + 20, label, "Sans600", 15, MUTED)
        x = 160
        for it in items:
            x += c.chip(x, y, it, tint) + 8
        assert x <= 840 - 24, f"stack row overflows: {label}"
        y += 42
    return c


if __name__ == "__main__":
    save("hero.svg", hero())
    for name, label, tint, icon in [("btn-portfolio.svg", "Portfolio", "clay", "globe"),
                                    ("btn-linkedin.svg", "LinkedIn", "blue", "in"),
                                    ("btn-email.svg", "Email", "sage", "mail"),
                                    ("btn-resume.svg", "Resume", "amber", "doc")]:
        save(name, button(label, tint, ICONS[icon]))
    save("project-fashion.svg", project(
        "Machine learning", "clay", "Fashion Recommendation System",
        "Hybrid recommender on the H&M dataset: collaborative filtering (TruncatedSVD) "
        "blended with content-based similarity, served by a Flask API.",
        ["Python", "scikit-learn", "Flask"]))
    save("project-warehouse.svg", project(
        "Data engineering", "sage", "E-Commerce Data Warehouse",
        "PostgreSQL star schema (a sales fact table and five dimensions) on the Olist "
        "dataset, loaded by a Python ETL pipeline.",
        ["PostgreSQL", "Python", "pygrametl"]))
    save("project-stadium.svg", project(
        "Backend", "blue", "Stadium Reservation Microservices",
        "Node.js microservices behind a REST + GraphQL gateway, talking over gRPC and "
        "publishing reservation events on Kafka.",
        ["Node.js", "gRPC", "Kafka", "GraphQL"]))
    save("project-injury.svg", project(
        "ML · sports data", "amber", "Soccer Player Injury Prediction",
        "Ranks next-season injury risk from earlier-season data, with a split grouped by "
        "player. ROC-AUC 0.69 vs 0.50 for chance.",
        ["Python", "XGBoost", "pandas"]))
    save("stack.svg", stack_card())
