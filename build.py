"""data/*.json을 template.html에 넣어 index.html, map.html을 만든다."""
import json
from pathlib import Path

root = Path(__file__).parent
html = (root / "template.html").read_text(encoding="utf-8")
for key, name in [("LGK", "lgk"), ("LIPE", "lipe")]:
    data = json.loads((root / "data" / f"{name}.json").read_text(encoding="utf-8"))
    html = html.replace(f"/*{key}*/", json.dumps(data, ensure_ascii=False))

for out in ("index.html", "map.html"):
    (root / out).write_text(html, encoding="utf-8")
print("built index.html, map.html")
