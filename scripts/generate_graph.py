#!/usr/bin/env python3
"""Génère generated/activity-graph.svg (contributions des 31 derniers jours)
avec la couleur du thème actif. Aucune dépendance externe.

Usage : GH_TOKEN=... python3 scripts/generate_graph.py
        python3 scripts/generate_graph.py --demo   (données factices, test local)
"""
import json, os, random, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "ALIX6S")
DAYS = 31

def accent():
    theme = (ROOT / "active-theme.txt").read_text().strip()
    for line in (ROOT / "themes" / theme / "theme.env").read_text().splitlines():
        if line.startswith("ACCENT="):
            return line.split("=", 1)[1].strip()
    return "d60cfe"

def fetch(token):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=DAYS + 1)
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){contributionsCollection(from:$from,to:$to){
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    body = json.dumps({"query": query, "variables": {
        "login": USER, "from": start.isoformat(), "to": now.isoformat()}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json",
        "User-Agent": "profile-graph"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in data:
        sys.exit(f"Erreur GraphQL : {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    return sorted(days.items())[-DAYS:]

def demo():
    random.seed(1)
    today = datetime.now(timezone.utc).date()
    return [((today - timedelta(days=DAYS - 1 - i)).isoformat(), random.choice([0, 0, 1, 2, 3, 5, 8]))
            for i in range(DAYS)]

def render(data, color):
    W, H, L, R, T, B = 900, 300, 50, 25, 60, 45
    pw, ph = W - L - R, H - T - B
    top = max(4, max(v for _, v in data))
    top += (-top) % 4                       # arrondi au multiple de 4
    X = lambda i: L + pw * i / (len(data) - 1)
    Y = lambda v: T + ph - ph * v / top
    pts = [(X(i), Y(v)) for i, (_, v) in enumerate(data)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{L},{T+ph} {line} {L+pw},{T+ph}"
    c = f"#{color}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
           f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{c}" stop-opacity="0.35"/>'
           f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient></defs>',
           f'<text x="{W/2}" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="{c}">'
           f'Contribution Evolution</text>']
    for k in range(5):                      # grille + axe Y
        v = top * k / 4; y = Y(v)
        out.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="{c}" stroke-opacity="0.18"/>')
        out.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{c}">{int(v)}</text>')
    for i, (d, _) in enumerate(data):       # axe X
        if i % 5 == 0 or i == len(data) - 1:
            dt = datetime.fromisoformat(d)
            out.append(f'<text x="{X(i):.1f}" y="{H-B+20}" text-anchor="middle" font-size="11" fill="{c}">'
                       f'{dt.day}/{dt.month}</text>')
    out.append(f'<polygon points="{area}" fill="url(#g)"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{c}" stroke-width="2.5" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for (x, y), (d, v) in zip(pts, data):
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{c}"><title>{d} : {v}</title></circle>')
    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    if "--demo" in sys.argv:
        data = demo()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GH_TOKEN manquant (utilise --demo pour tester sans token)")
        data = fetch(token)
    (ROOT / "generated").mkdir(exist_ok=True)
    (ROOT / "generated" / "activity-graph.svg").write_text(render(data, accent()), encoding="utf-8")
    print(f"✔ generated/activity-graph.svg ({len(data)} jours, couleur #{accent()})")
