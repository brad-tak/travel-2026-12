"""data/*.json을 template.html에 넣어 index.html, map.html을 만든다.

숙소(cat=hotel)에서 각 장소까지의 도보·차 경로를 OSM 라우터로 계산해 data/routes.json에 캐시한다.
"""
import json
import math
import time
import urllib.request
from pathlib import Path

root = Path(__file__).parent
ROUTER = "https://routing.openstreetmap.de/routed-{mode}/route/v1/driving/{a};{b}?overview=false"
MODES = {"lgk": ["foot", "car"]}
# 꼬리페는 차가 없고, OSM 보행로가 끊겨 있어 경로가 실제의 3~7배로 나온다
# → 직선거리 × 우회계수, 시속 4km로 추정
LIPE_DETOUR = 1.3
WALK_MPS = 4000 / 3600


def estimate_walk(src, dst):
    p1, p2 = math.radians(src["lat"]), math.radians(dst["lat"])
    dp, dl = p2 - p1, math.radians(dst["lon"] - src["lon"])
    straight = 2 * 6371000 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
    m = straight * LIPE_DETOUR
    return {"m": int(round(m, -1)), "s": round(m / WALK_MPS), "est": True}

cache_path = root / "data" / "routes.json"
cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}


def route(mode, src, dst):
    key = f"{mode}:{src['lat']},{src['lon']}->{dst['lat']},{dst['lon']}"
    if key not in cache:
        url = ROUTER.format(mode=mode, a=f"{src['lon']},{src['lat']}", b=f"{dst['lon']},{dst['lat']}")
        req = urllib.request.Request(url, headers={"User-Agent": "trip-planner/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.load(r)
        rt = res["routes"][0] if res.get("code") == "Ok" else None
        cache[key] = {"m": round(rt["distance"]), "s": round(rt["duration"])} if rt else None
        time.sleep(0.5)
    return cache[key]


html = (root / "template.html").read_text(encoding="utf-8")
for key, name in [("LGK", "lgk"), ("LIPE", "lipe")]:
    data = json.loads((root / "data" / f"{name}.json").read_text(encoding="utf-8"))
    hotel = next(p for p in data if p["cat"] == "hotel")
    for p in data:
        if p is hotel or p["lat"] is None or p.get("transport"):
            continue
        if name == "lipe":
            p["routes"] = {"foot": estimate_walk(hotel, p)}
        else:
            p["routes"] = {mode: route(mode, hotel, p) for mode in MODES[name]}
    html = html.replace(f"/*{key}*/", json.dumps(data, ensure_ascii=False))

cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
for out in ("index.html", "map.html"):
    (root / out).write_text(html, encoding="utf-8")
print("built index.html, map.html")
