#!/usr/bin/env python3
"""
Builds the static artwork for the profile README (header + section banners).

Text is converted to vector outlines using the bundled Orbitron / Space Mono
fonts, so the art looks identical on every device (GitHub can't load web fonts
inside README images).

Edit the TEXT section below, then run:
    pip install fonttools brotli
    python scripts/build_banners.py
"""

import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
FONTS = os.path.join(HERE, "fonts")

# ── TEXT — edit me ─────────────────────────────────────────────────────────
NAME = "JUDEA TABLATE"
ROLE = "BACKEND ENGINEER // SOFTWARE ENGINEERING // APPLIED AI"
HUD_TL = "SYS://JUDEA.TABLATE"
HUD_TR = "MNL.PH  14.60N 120.98E"
HUD_BL = "FEU TECH  ·  BSCS-SE"
HUD_BR = "INTERN @ FLYRANK AI"
SECTIONS = [  # (file, index, title, tag)
    ("sec-about.svg", "01", "CURRENT ORBIT", "who i am"),
    ("sec-projects.svg", "02", "SELECTED BUILDS", "things i made"),
    ("sec-stack.svg", "03", "TECH ARSENAL", "tools of the trade"),
    ("sec-experience.svg", "04", "EXPERIENCE LOG", "where i've been"),
    ("sec-telemetry.svg", "05", "LIVE TELEMETRY", "auto-synced daily"),
]

# ── palette ────────────────────────────────────────────────────────────────
BG, GRID = "#0A090D", "#2A2430"
PINK, PINK_SOFT, PINK_PALE = "#FF4FA3", "#FF8CC6", "#FFC2E0"
SILVER, SILVER_DIM = "#E6E6EE", "#9C9AA8"


class Font:
    def __init__(self, file):
        self.f = TTFont(os.path.join(FONTS, file))
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]

    def width(self, text, size, spacing=0):
        s = size / self.upm
        w = sum(self.hmtx[self.cmap.get(ord(c), ".notdef")][0] * s + spacing for c in text)
        return w - spacing if text else 0

    def path(self, text, x, y, size, spacing=0, anchor="start"):
        """Returns an SVG path 'd' for text with its baseline at y."""
        s = size / self.upm
        if anchor == "middle":
            x -= self.width(text, size, spacing) / 2
        elif anchor == "end":
            x -= self.width(text, size, spacing)
        pen = SVGPathPen(self.gs)
        for ch in text:
            g = self.cmap.get(ord(ch), ".notdef")
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
            x += self.hmtx[g][0] * s + spacing
        return pen.getCommands()


ORB9 = Font("orbitron-latin-900-normal.woff")
ORB7 = Font("orbitron-latin-700-normal.woff")
MONO = Font("space-mono-latin-400-normal.woff")
MONO7 = Font("space-mono-latin-700-normal.woff")

HEART = "M0 3.2C0-1 5.6-1.6 6.6 2.2 7.6-1.6 13.2-1 13.2 3.2 13.2 7 8.4 9.8 6.6 12 4.8 9.8 0 7 0 3.2Z"

CHROME = f"""
    <linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset=".38" stop-color="{SILVER}"/>
      <stop offset=".52" stop-color="#8E8C9C"/><stop offset=".6" stop-color="#C9C8D4"/>
      <stop offset="1" stop-color="#FFFFFF"/>
    </linearGradient>
    <linearGradient id="pinkline" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{PINK}"/><stop offset=".6" stop-color="{PINK_SOFT}"/>
      <stop offset="1" stop-color="{SILVER}" stop-opacity="0"/>
    </linearGradient>"""


def header():
    W, H, HZ = 1200, 360, 250  # HZ = horizon line
    cx = W / 2
    name_d = ORB9.path(NAME, cx, 168, 78, spacing=6, anchor="middle")
    role_d = MONO7.path(ROLE, cx, 212, 15, spacing=3.2, anchor="middle")
    role_w = MONO7.width(ROLE, 15, 3.2)

    # perspective floor
    floor = []
    for i in range(-14, 15):
        floor.append(f'<line x1="{cx}" y1="{HZ}" x2="{cx + i*95}" y2="{H}"/>')
    hlines = []
    for k in range(10):
        t = k / 10
        y = HZ + (H - HZ) * t * t
        hlines.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"/>')

    # synthwave sun stripes
    sun_cuts = "".join(
        f'<rect x="{cx-170}" y="{HZ - 14 - i*13}" width="340" height="{4 - i*0.35:.2f}"/>' for i in range(7)
    )

    sparks = ""
    for i, (x, y, r, d) in enumerate([(120, 70, 1.6, 0), (260, 120, 1.2, .8), (980, 80, 1.8, .4), (1090, 150, 1.2, 1.2),
                                       (420, 52, 1.0, 1.6), (820, 46, 1.3, 2.0), (60, 190, 1.1, .6), (1140, 210, 1.4, 1.4)]):
        sparks += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{PINK_PALE if i % 2 else SILVER}">'
                   f'<animate attributeName="opacity" values=".15;1;.15" dur="3s" begin="{d}s" repeatCount="indefinite"/></circle>')

    hud = f'<g fill="{SILVER_DIM}">' + "".join([
        f'<path d="{MONO.path(HUD_TL, 52, 42, 11, 2)}"/>',
        f'<path d="{MONO.path(HUD_TR, W-52, 42, 11, 2, "end")}"/>',
        f'<path d="{MONO.path(HUD_BL, 52, H-26, 11, 2)}" fill="{SILVER}"/>',
        f'<path d="{MONO.path(HUD_BR, W-52, H-26, 11, 2, "end")}" fill="{SILVER}"/>',
    ]) + "</g>"
    online_x = 52 + MONO.width(HUD_TL, 11, 2) + 18

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME} — {ROLE}">
  <defs>{CHROME}
    <radialGradient id="glow" cx=".5" cy="{HZ/H:.2f}" r=".6">
      <stop offset="0" stop-color="{PINK}" stop-opacity=".45"/><stop offset=".5" stop-color="{PINK}" stop-opacity=".08"/>
      <stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{SILVER}"/><stop offset=".45" stop-color="{PINK_SOFT}"/><stop offset="1" stop-color="{PINK}"/>
    </linearGradient>
    <linearGradient id="floorfade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".25" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff"/>
    </linearGradient>
    <mask id="floormask"><rect x="0" y="{HZ}" width="{W}" height="{H-HZ}" fill="url(#floorfade)"/></mask>
    <mask id="sunmask"><rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{sun_cuts}</g></mask>
    <clipPath id="sky"><rect width="{W}" height="{HZ}"/></clipPath>
    <clipPath id="frame"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16"/></clipPath>
    <clipPath id="roleclip"><rect x="{cx - role_w/2 - 4}" y="190" height="34" width="0">
      <animate attributeName="width" from="0" to="{role_w + 8:.0f}" dur="2.2s" begin=".6s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1" keyTimes="0;1"/>
    </rect></clipPath>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".95"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="nameclip"><path d="{name_d}"/></clipPath>
    <filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
  </defs>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
    {sparks}

    <!-- sun -->
    <g clip-path="url(#sky)" opacity=".55">
      <circle cx="{cx}" cy="{HZ}" r="150" fill="url(#sun)" mask="url(#sunmask)"/>
    </g>

    <!-- perspective floor -->
    <g mask="url(#floormask)" stroke="{PINK}" stroke-width="1.1" opacity=".55">
      {''.join(floor)}
      <g>
        {''.join(hlines)}
        <animateTransform attributeName="transform" type="translate" values="0 0; 0 11" dur="1.2s" repeatCount="indefinite"/>
      </g>
    </g>
    <line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="{PINK_SOFT}" stroke-width="1.6"/>
    <line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="{PINK}" stroke-width="7" opacity=".35" filter="url(#blur)"/>

    <!-- name -->
    <path d="{name_d}" fill="{PINK}" opacity=".75" filter="url(#blur)">
      <animate attributeName="opacity" values=".45;.85;.45" dur="4s" repeatCount="indefinite"/>
    </path>
    <path d="{name_d}" fill="url(#chrome)" stroke="#FFFFFF" stroke-opacity=".35" stroke-width=".8"/>
    <g clip-path="url(#nameclip)">
      <rect x="-300" y="80" width="180" height="110" fill="url(#shine)" transform="skewX(-20)">
        <animate attributeName="x" values="-300;1500" dur="3.6s" begin="1s" repeatCount="indefinite"/>
      </rect>
    </g>

    <!-- role line (types itself in) -->
    <path d="{role_d}" fill="{PINK_SOFT}" clip-path="url(#roleclip)"/>
    <rect x="{cx - 260}" y="231.5" width="520" height="1" fill="url(#pinkline)" opacity="0">
      <animate attributeName="opacity" to=".8" dur=".5s" begin="2.6s" fill="freeze"/>
    </rect>

    <!-- HUD -->
    {hud}
    <circle cx="{online_x}" cy="38" r="4" fill="{PINK}">
      <animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/>
    </circle>
    <path d="{MONO7.path('ONLINE', online_x + 12, 42, 11, 2)}" fill="{PINK}"/>

    <!-- scanline -->
    <rect x="0" y="0" width="{W}" height="2" fill="{SILVER}" opacity=".08">
      <animate attributeName="y" values="0;{H}" dur="6s" repeatCount="indefinite"/>
    </rect>
  </g>

  <!-- frame + HUD brackets -->
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="{PINK}" stroke-opacity=".45" stroke-width="1.5"/>
  <g stroke="{PINK}" stroke-width="2.5" fill="none" stroke-linecap="square">
    <path d="M22 50V22H50"/><path d="M{W-50} 22H{W-22}V50"/>
    <path d="M22 {H-50}V{H-22}H50"/><path d="M{W-50} {H-22}H{W-22}V{H-50}"/>
  </g>
</svg>
"""


def section(index, title, tag):
    W, H = 1000, 64
    t_d = ORB7.path(title, 78, 41, 22, spacing=4)
    t_w = ORB7.width(title, 22, 4)
    i_d = ORB9.path(index, 18, 42, 24, spacing=1)
    tag_text = f"// {tag}"
    tag_d = MONO.path(tag_text, W - 18, 41, 12, 1.5, "end")
    tag_w = MONO.width(tag_text, 12, 1.5)
    lx0, lx1 = 78 + t_w + 22, W - 18 - tag_w - 20
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{index} {title}">
  <defs>{CHROME}</defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="{BG}" stroke="{GRID}"/>
  <path d="M8 10H60L68 18V54H16L8 46Z" fill="none" stroke="{PINK}" stroke-width="1.5"/>
  <path d="{i_d}" fill="{PINK}"/>
  <path d="{t_d}" fill="url(#chrome)"/>
  <rect x="{lx0}" y="32.4" width="{lx1-lx0:.1f}" height="1.2" fill="url(#pinkline)"/>
  <rect x="{lx0 - 4}" y="29" width="8" height="8" fill="{PINK}" transform="rotate(45 {lx0} 33)"/>
  <circle cx="{lx0}" cy="33" r="3" fill="{PINK_PALE}">
    <animate attributeName="cx" values="{lx0};{lx1};{lx0}" dur="7s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;.2;1" dur="7s" repeatCount="indefinite"/>
  </circle>
  <path d="{tag_d}" fill="{SILVER_DIM}"/>
</svg>
"""


def footer():
    W, H = 1000, 120
    a = "END OF TRANSMISSION"
    b = "crafted with intention  ·  black, pink & silver  ·  manila, ph"
    a_d = ORB7.path(a, W / 2, 58, 18, 6, "middle")
    a_w = ORB7.width(a, 18, 6)
    b_d = MONO.path(b, W / 2, 88, 11, 1.6, "middle")
    hx = W / 2 + a_w / 2 + 14
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="End of transmission — thanks for stopping by">
  <defs>{CHROME}
    <linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{PINK}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="{GRID}"/>
  <rect x="60" y="18" width="{W-120}" height="1.2" fill="url(#fade)"/>
  <path d="{a_d}" fill="url(#chrome)"/>
  <g transform="translate({hx:.1f} 44)">
    <path d="{HEART}" fill="{PINK}">
      <animate attributeName="opacity" values="1;.35;1" dur="1.2s" repeatCount="indefinite"/>
    </path>
  </g>
  <path d="{b_d}" fill="{SILVER_DIM}"/>
  <rect x="60" y="102" width="{W-120}" height="1.2" fill="url(#fade)" opacity=".5"/>
</svg>
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {"header.svg": header(), "footer.svg": footer()}
    for file, idx, title, tag in SECTIONS:
        files[file] = section(idx, title, tag)
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", name)


if __name__ == "__main__":
    main()
