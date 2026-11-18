#!/usr/bin/env python3
"""
Generates self-hosted, pink & silver GitHub stat cards for the profile README.

Writes three SVGs into ./assets:
  stats.svg      – contributions, commits, PRs, issues, stars, repos
  languages.svg  – top languages by bytes across your public, non-fork repos
  activity.svg   – last 30 days of contributions + current / longest streak

No third-party services are used, so the cards can't go down or get rate-limited.

Env vars:
  GH_TOKEN        token used for the GitHub GraphQL API (the workflow passes one in)
  GH_USER         GitHub username (defaults to the repo owner)
  EXCLUDE_LANGS   comma-separated languages to hide, e.g. "Jupyter Notebook,CSS"
  EXCLUDE_REPOS   comma-separated repo names to skip for the language card

Usage:
  python scripts/generate_cards.py              # real data
  python scripts/generate_cards.py --placeholder  # "syncing" cards, no API calls
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# ── palette ────────────────────────────────────────────────────────────────
BG = "#0A090D"
PANEL = "#121017"
GRID = "#2A2430"
PINK = "#FF4FA3"
PINK_SOFT = "#FF8CC6"
SILVER = "#E6E6EE"
SILVER_DIM = "#9C9AA8"
LANG_COLORS = ["#FF4FA3", "#FF8CC6", "#FFC2E0", "#E6E6EE", "#B8B8C6", "#7E7C8C"]
FONT = "'JetBrains Mono','SFMono-Regular','Cascadia Code',Consolas,'Liberation Mono',monospace"

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    login
    name
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


# ── data ───────────────────────────────────────────────────────────────────
def gql(token, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def fetch(token, login):
    user, repos, cursor = None, [], None
    while True:
        page = gql(token, {"login": login, "cursor": cursor})
        user = user or page
        repos += page["repositories"]["nodes"]
        info = page["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        cursor = info["endCursor"]

    skip_langs = {s.strip().lower() for s in os.getenv("EXCLUDE_LANGS", "").split(",") if s.strip()}
    skip_repos = {s.strip().lower() for s in os.getenv("EXCLUDE_REPOS", "").split(",") if s.strip()}

    langs = {}
    for repo in repos:
        if repo["name"].lower() in skip_repos:
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name.lower() in skip_langs:
                continue
            langs[name] = langs.get(name, 0) + edge["size"]

    cc = user["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])

    return {
        "login": user["login"],
        "name": user["name"] or user["login"],
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": user["repositories"]["totalCount"],
        "contributed_to": user["repositoriesContributedTo"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "langs": sorted(langs.items(), key=lambda kv: kv[1], reverse=True),
        "days": days,
    }


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    current = 0
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today not counted yet — don't break the streak
        i -= 1
    while i >= 0 and counts[i] > 0:
        current += 1
        i -= 1
    return current, longest


def fmt(n):
    return f"{n/1000:.1f}k" if n >= 10000 else f"{n:,}"


# ── shared svg bits ────────────────────────────────────────────────────────
def defs(uid):
    return f"""
  <defs>
    <linearGradient id="{uid}-silver" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset=".45" stop-color="{SILVER}"/>
      <stop offset=".7" stop-color="#A9A7B6"/><stop offset="1" stop-color="#F3F3F8"/>
    </linearGradient>
    <linearGradient id="{uid}-pink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_SOFT}"/>
    </linearGradient>
    <linearGradient id="{uid}-edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{PINK}" stop-opacity=".9"/>
      <stop offset=".5" stop-color="{SILVER_DIM}" stop-opacity=".35"/>
      <stop offset="1" stop-color="{PINK_SOFT}" stop-opacity=".9"/>
    </linearGradient>
    <pattern id="{uid}-grid" width="18" height="18" patternUnits="userSpaceOnUse">
      <path d="M18 0H0V18" fill="none" stroke="{GRID}" stroke-width=".6" opacity=".55"/>
    </pattern>
    <radialGradient id="{uid}-glow" cx=".85" cy="0" r=".9">
      <stop offset="0" stop-color="{PINK}" stop-opacity=".22"/>
      <stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
    </radialGradient>
  </defs>"""


STYLE = f"""
  <style>
    text {{ font-family: {FONT}; }}
    .t  {{ fill: {SILVER}; font-size: 12px; letter-spacing: 2px; font-weight: 700; }}
    .lb {{ fill: {SILVER_DIM}; font-size: 11px; letter-spacing: 1.2px; }}
    .v  {{ fill: {SILVER}; font-size: 13px; font-weight: 700; }}
    .sm {{ fill: {SILVER_DIM}; font-size: 9px; letter-spacing: 1.5px; }}
    .fade {{ opacity: 0; animation: in .6s ease-out forwards; }}
    .scan {{ animation: scan 5s linear infinite; }}
    .blink {{ animation: blink 1.6s steps(2) infinite; }}
    @keyframes in {{ to {{ opacity: 1; }} }}
    @keyframes scan {{ 0% {{ transform: translateY(-20px); }} 100% {{ transform: translateY(240px); }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  </style>"""


def frame(uid, w, h, title, tag):
    """Dark panel with grid, glow, HUD corner brackets and a title bar."""
    c = 14  # bracket length
    return f"""
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{BG}"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="url(#{uid}-grid)"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="url(#{uid}-glow)"/>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="none" stroke="url(#{uid}-edge)" stroke-width="1.2"/>
  <g stroke="{PINK}" stroke-width="2" fill="none">
    <path d="M6 {6+c}V6H{6+c}"/><path d="M{w-6-c} 6H{w-6}V{6+c}"/>
    <path d="M6 {h-6-c}V{h-6}H{6+c}"/><path d="M{w-6-c} {h-6}H{w-6}V{h-6-c}"/>
  </g>
  <g clip-path="url(#{uid}-clip)">
    <rect class="scan" x="0" y="0" width="{w}" height="2" fill="{PINK}" opacity=".18"/>
  </g>
  <clipPath id="{uid}-clip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10"/></clipPath>
  <circle cx="26" cy="27" r="3.5" fill="{PINK}" class="blink"/>
  <text x="38" y="31" class="t" fill="url(#{uid}-silver)">{escape(title)}</text>
  <text x="{w-22}" y="31" class="sm" text-anchor="end">{escape(tag)}</text>
  <line x1="22" y1="44" x2="{w-22}" y2="44" stroke="url(#{uid}-pink)" stroke-width="1" opacity=".55"/>"""


def svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}">{body}\n</svg>\n'
    )


# ── cards ──────────────────────────────────────────────────────────────────
def stats_card(d):
    uid, w, h = "st", 495, 210
    year = dt.date.today().year
    rows = [
        ("CONTRIBUTIONS · 1Y", fmt(d["contributions"])),
        (f"COMMITS · {year}", fmt(d["commits"])),
        ("PULL REQUESTS", fmt(d["prs"])),
        ("ISSUES", fmt(d["issues"])),
        ("STARS EARNED", fmt(d["stars"])),
        ("PUBLIC REPOS", fmt(d["repos"])),
    ]
    body = defs(uid) + STYLE + frame(uid, w, h, "SYSTEM.STATS", f"@{d['login']}".upper())
    y0 = 72
    for i, (label, value) in enumerate(rows):
        y = y0 + i * 22
        body += f"""
  <g class="fade" style="animation-delay:{.15 + i*.1:.2f}s">
    <rect x="26" y="{y-8}" width="4" height="4" fill="{PINK}" transform="rotate(45 28 {y-6})"/>
    <text x="40" y="{y-2}" class="lb">{label}</text>
    <line x1="190" y1="{y-6}" x2="268" y2="{y-6}" stroke="{GRID}" stroke-dasharray="2 4"/>
    <text x="300" y="{y-2}" class="v" text-anchor="end">{value}</text>
  </g>"""

    # ring: contributed-to + followers, ring fill = share of days active
    days = d["days"]
    active = sum(1 for x in days if x["contributionCount"] > 0)
    pct = active / len(days) if days else 0
    r, cx, cy = 50, 400, 122
    circ = 2 * 3.14159 * r
    body += f"""
  <g class="fade" style="animation-delay:.3s">
    <circle cx="{cx}" cy="{cy}" r="{r+9}" fill="none" stroke="{GRID}" stroke-dasharray="1 5"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1E1A24" stroke-width="8"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#{uid}-pink)" stroke-width="8"
      stroke-linecap="round" transform="rotate(-90 {cx} {cy})"
      stroke-dasharray="{circ*pct:.1f} {circ:.1f}" stroke-dashoffset="{circ*pct:.1f}"
      style="animation: draw 1.4s ease-out .4s forwards"/>
    <text x="{cx}" y="{cy+2}" text-anchor="middle" style="font-size:24px;font-weight:800" fill="url(#{uid}-silver)">{round(pct*100)}%</text>
    <text x="{cx}" y="{cy+19}" text-anchor="middle" class="sm">DAYS ACTIVE</text>
    <text x="{cx}" y="{cy+r+26}" text-anchor="middle" class="sm">{d['followers']} FOLLOWERS · {d['contributed_to']} COLLABS</text>
  </g>"""
    return svg(w, h, body, f"GitHub stats for {d['login']}")


def languages_card(d):
    uid, w, h = "lg", 495, 210
    top = d["langs"][:6]
    total = sum(s for _, s in top) or 1
    body = defs(uid) + STYLE + frame(uid, w, h, "LANG.MATRIX", "BY BYTES · PUBLIC REPOS")

    # segmented bar
    x, bw = 26, w - 52
    body += f'\n  <rect x="{x}" y="62" width="{bw}" height="10" rx="5" fill="#1E1A24"/>'
    body += f'\n  <g style="transform-origin:{x}px 67px; animation: grow 1s ease-out forwards; transform: scaleX(0)">'
    body += f'<clipPath id="{uid}-bar"><rect x="{x}" y="62" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#{uid}-bar)">'
    cur = x
    for i, (_, size) in enumerate(top):
        seg = bw * size / total
        body += f'<rect x="{cur:.1f}" y="62" width="{seg+0.5:.1f}" height="10" fill="{LANG_COLORS[i]}"/>'
        cur += seg
    body += "</g></g>"

    # two-column legend
    for i, (name, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 26 + col * 230, 104 + row * 34
        p = size / total * 100
        body += f"""
  <g class="fade" style="animation-delay:{.3 + i*.1:.2f}s">
    <rect x="{lx}" y="{ly-10}" width="10" height="10" rx="2" fill="{LANG_COLORS[i]}"/>
    <text x="{lx+18}" y="{ly-1}" class="v">{escape(name)}</text>
    <text x="{lx+212}" y="{ly-1}" class="lb" text-anchor="end">{p:.1f}%</text>
    <rect x="{lx+18}" y="{ly+6}" width="194" height="2" fill="#1E1A24"/>
    <rect x="{lx+18}" y="{ly+6}" width="{194*p/100:.1f}" height="2" fill="{LANG_COLORS[i]}" opacity=".8"/>
  </g>"""
    if not top:
        body += f'\n  <text x="{w/2}" y="130" text-anchor="middle" class="lb">NO LANGUAGE DATA YET</text>'
    return svg(w, h, body, f"Top languages for {d['login']}")


def activity_card(d):
    uid, w, h = "ac", 1000, 230
    days = d["days"][-30:]
    cur, longest = streaks(d["days"])
    body = defs(uid) + STYLE + frame(uid, w, h, "ACTIVITY.LOG // LAST 30 DAYS", "CONTRIBUTION SIGNAL")

    # chart area
    cx0, cx1, cy0, cy1 = 40, 690, 64, 196
    peak = max([x["contributionCount"] for x in days] + [1])
    n = max(len(days) - 1, 1)
    pts = [
        (cx0 + (cx1 - cx0) * i / n, cy1 - (cy1 - cy0) * x["contributionCount"] / peak)
        for i, x in enumerate(days)
    ]
    for gy in range(4):
        yy = cy0 + (cy1 - cy0) * gy / 3
        body += f'\n  <line x1="{cx0}" y1="{yy:.1f}" x2="{cx1}" y2="{yy:.1f}" stroke="{GRID}" stroke-dasharray="2 5"/>'
    if pts:
        line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        area = f"{cx0},{cy1} {line} {cx1},{cy1}"
        length = sum(
            ((pts[i][0]-pts[i-1][0])**2 + (pts[i][1]-pts[i-1][1])**2) ** .5 for i in range(1, len(pts))
        ) + 10
        body += f"""
  <linearGradient id="{uid}-fill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{PINK}" stop-opacity=".35"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
  </linearGradient>
  <polygon points="{area}" fill="url(#{uid}-fill)" class="fade" style="animation-delay:.8s"/>
  <polyline points="{line}" fill="none" stroke="url(#{uid}-pink)" stroke-width="2.4" stroke-linejoin="round"
    stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}" style="animation: draw 1.8s ease-out forwards"/>"""
        for i, (px, py) in enumerate(pts):
            if days[i]["contributionCount"] > 0:
                body += f'\n  <circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{BG}" stroke="{SILVER}" stroke-width="1.4" class="fade" style="animation-delay:{1.2 + i*.02:.2f}s"/>'
        first = dt.date.fromisoformat(days[0]["date"]).strftime("%b %d").upper()
        last = dt.date.fromisoformat(days[-1]["date"]).strftime("%b %d").upper()
        body += f'\n  <text x="{cx0}" y="{cy1+18}" class="sm">{first}</text>'
        body += f'\n  <text x="{cx1}" y="{cy1+18}" class="sm" text-anchor="end">{last}</text>'
        body += f'\n  <text x="{cx0-8}" y="{cy0+4}" class="sm" text-anchor="end">{peak}</text>'
        body += f'\n  <text x="{cx0-8}" y="{cy1}" class="sm" text-anchor="end">0</text>'

    # streak readouts
    tiles = [("CURRENT STREAK", f"{cur}", "DAYS"), ("LONGEST STREAK", f"{longest}", "DAYS"),
             ("30-DAY TOTAL", f"{sum(x['contributionCount'] for x in days)}", "CONTRIBS")]
    for i, (label, value, unit) in enumerate(tiles):
        tx, ty = 730, 62 + i * 52
        body += f"""
  <g class="fade" style="animation-delay:{.4 + i*.15:.2f}s">
    <rect x="{tx}" y="{ty}" width="244" height="44" rx="6" fill="{PANEL}" stroke="{GRID}"/>
    <rect x="{tx}" y="{ty}" width="3" height="44" rx="1.5" fill="url(#{uid}-pink)"/>
    <text x="{tx+16}" y="{ty+27}" class="lb">{label}</text>
    <text x="{tx+228}" y="{ty+30}" text-anchor="end" style="font-size:22px;font-weight:800" fill="url(#{uid}-silver)">{value}<tspan class="sm" dx="6">{unit}</tspan></text>
  </g>"""
    return svg(w, h, body, f"Recent GitHub activity for {d['login']}")


def placeholder():
    uid, cards = "ph", {}
    for name, (w, h, title) in {
        "stats.svg": (495, 210, "SYSTEM.STATS"),
        "languages.svg": (495, 210, "LANG.MATRIX"),
        "activity.svg": (1000, 230, "ACTIVITY.LOG"),
    }.items():
        body = defs(uid) + STYLE + frame(uid, w, h, title, "SYNCING")
        body += f'\n  <text x="{w/2}" y="{h/2+14}" text-anchor="middle" class="lb">ESTABLISHING UPLINK<tspan class="blink" fill="{PINK}"> _</tspan></text>'
        cards[name] = svg(w, h, body, f"{title} – syncing")
    return cards


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if "--placeholder" in sys.argv:
        cards = placeholder()
    else:
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        login = os.getenv("GH_USER") or os.getenv("GITHUB_REPOSITORY_OWNER")
        if not token or not login:
            raise SystemExit("Set GH_TOKEN and GH_USER (or run inside GitHub Actions).")
        data = fetch(token, login)
        cards = {
            "stats.svg": stats_card(data),
            "languages.svg": languages_card(data),
            "activity.svg": activity_card(data),
        }
    for name, content in cards.items():
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", name)


if __name__ == "__main__":
    main()
