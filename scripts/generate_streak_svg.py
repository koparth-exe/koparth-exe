#!/usr/bin/env python3
"""Generate an animated GitHub-streak SVG with terminal frame and stats footer.
Runs in a GitHub Action daily to stay live.
"""
import sys, json, os, datetime, urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "koparth-exe"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "streak.svg"

def get_data(user):
    # Try fetching local contrib.json first or use the api
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrib.json")
    if os.path.exists(here):
        return json.load(open(here))
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.loads(r.read().decode())

data = get_data(USER)
contribs = data["contributions"]
total = data["total"]["lastYear"]

# ---- layout with terminal header and stats footer ----
CELL, GAP, RAD = 12, 3, 2.5
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 25
TITLEBAR_H = 30
STATS_H = 88

n = len(contribs)
NW = (n + 6) // 7
ART_W = NW * STEP
W = PAD + LEFT_LABEL_W + art_w + PAD
H = TITLEBAR_H + TOP_LABEL_H + (7 * STEP) + STATS_H + PAD

COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
GRAY = "#7d8590"
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

REVEAL, DUR = 3.6, 0.55
maxorder = (NW-1) + 6*0.55

rects, labels = [], []
sd = datetime.date.fromisoformat(contribs[0]["date"])
last_m = None
grid_top = TITLEBAR_H + TOP_LABEL_H
grid_left = PAD + LEFT_LABEL_W

for wk in range(NW):
    d = sd + datetime.timedelta(days=wk*7)
    if d.month != last_m:
        last_m = d.month
        labels.append(f'<text class="lbl" x="{grid_left + wk*STEP}" y="{TITLEBAR_H + 16}">{MONTHS[d.month-1]}</text>')

for name, r in [(1,"Mon"), (3,"Wed"), (5,"Fri")]:
    y = grid_top + r * STEP + CELL * 0.78
    labels.append(f'<text class="lbl" x="{PAD}" y="{y:.1f}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i//7, i%7, c["level"]
    gx = grid_left + wk*STEP
    gy = grid_top + row*STEP
    delay = round((wk + row*0.55)/maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c"
    count = c["count"]
    date_s = c["date"]
    rects.append(
        f'<rect class="{cls}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s">'
        f'<title>{date_s}: {count} contributions</title></rect>'
    )

# Calculate dynamic stats if available in data
active_days = sum(1 for d in contribs if d["count"] > 0)
best = max(contribs, key=lambda d: d["count"])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<style>
  text.lbl {{ fill:{GRAY}; font-size:10px; font-weight:600; }}
  text.total {{ fill:#39d353; font-size:13px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" rx="12" fill="#0d1420"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#1f6feb" stroke-opacity="0.55"/>
<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="#1f6feb" stroke-opacity="0.35"/>
<circle cx="{PAD}" cy="{TITLEBAR_H/2}" r="5" fill="#ff5f56"/>
<circle cx="{PAD + 16}" cy="{TITLEBAR_H/2}" r="5" fill="#ffbd2e"/>
<circle cx="{PAD + 32}" cy="{TITLEBAR_H/2}" r="5" fill="#27c93f"/>
<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{GRAY}" font-size="12" text-anchor="middle">parth@github: ~/contributions --graph</text>

{''.join(labels)}
{''.join(rects)}

<line x1="0" y1="{grid_top + (7*STEP) + 8}" x2="{W}" y2="{grid_top + (7*STEP) + 8}" stroke="#1f6feb" stroke-opacity="0.25"/>

<text x="{PAD}" y="{grid_top + (7*STEP) + 32}" font-size="13" fill="#39d353">
  <tspan font-weight="700">{total:,}</tspan>
  <tspan fill="{GRAY}"> contributions in the last year</tspan>
</text>
<text x="{W - PAD}" y="{grid_top + (7*STEP) + 32}" font-size="12" fill="{GRAY}" text-anchor="end">
  {contribs[0]["date"]} &#8594; {contribs[-1]["date"]}
</text>

<text x="{PAD}" y="{grid_top + (7*STEP) + 58}" font-size="13" fill="{GRAY}">
  active days <tspan fill="#22d3ee" font-weight="700">{active_days}</span
  ><tspan fill="{GRAY}">   &#183;   best day </tspan>
  <tspan fill="#f2cc60" font-weight="700">{best["count"]}</tspan><tspan fill="{GRAY}"> on {best["date"]}</tspan>
</text>

</svg>'''

open(OUT, "w").write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} contributions")
