"""Situação agora em Maringá: METAR do aeroporto (SBMG) e ecos do radar (RainViewer) em volta da cidade.
Grava lab/sondagem_agora.json."""
import io, json, math, datetime as dt, requests
from PIL import Image
UA = {"User-Agent": "chuva-maringa"}
LAT, LON, Z = -23.42, -51.94, 7
out = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat()}
try:
    r = requests.get("https://aviationweather.gov/api/data/metar", params={"ids": "SBMG", "hours": 4, "format": "raw"}, headers=UA, timeout=30)
    out["metar"] = r.text.strip().splitlines()
except Exception as e: out["metar_erro"] = str(e)
def tile(lat, lon, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y
try:
    j = requests.get("https://api.rainviewer.com/public/weather-maps.json", headers=UA, timeout=30).json()
    fr = j["radar"]["past"][-4:]; fx, fy = tile(LAT, LON, Z); tx, ty = int(fx), int(fy)
    px, py = (fx - tx + 1) * 256, (fy - ty + 1) * 256  # posição de Maringá no mosaico 3x3
    kmpx = 2 * math.pi * 6371 * math.cos(math.radians(LAT)) / (256 * 2 ** Z)
    quadros = []
    for f in fr:
        img = Image.new("RGBA", (768, 768))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                u = f"{j['host']}{f['path']}/256/{Z}/{tx+dx}/{ty+dy}/0/0_0.png"
                t = requests.get(u, headers=UA, timeout=30)
                if t.status_code == 200: img.paste(Image.open(io.BytesIO(t.content)).convert("RGBA"), ((dx + 1) * 256, (dy + 1) * 256))
        p = img.load(); aneis = {"0-15": [0, 0], "15-40": [0, 0], "40-80": [0, 0], "80-150": [0, 0]}
        setores = {k: 0 for k in ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]}; forte = []
        for yy in range(768):
            for xx in range(768):
                d = math.hypot(xx - px, yy - py) * kmpx
                if d > 150: continue
                rr, gg, bb, aa = p[xx, yy]
                k = "0-15" if d < 15 else "15-40" if d < 40 else "40-80" if d < 80 else "80-150"
                aneis[k][1] += 1
                if aa > 0 and rr > 0:
                    aneis[k][0] += 1
                    az = (math.degrees(math.atan2(xx - px, py - yy)) + 360) % 360
                    if d >= 5: setores[["N", "NE", "L", "SE", "S", "SO", "O", "NO"][int((az + 22.5) // 45) % 8]] += 1
                    forte.append((rr, round(d), round(az)))
        forte.sort(reverse=True)
        quadros.append({"hora_utc": dt.datetime.fromtimestamp(f["time"], dt.timezone.utc).strftime("%H:%M"),
                        "cobertura_%": {k: round(100 * a / b, 1) if b else None for k, (a, b) in aneis.items()},
                        "pixels_por_setor": setores, "mais_intensos(valor,km,az)": forte[:8],
                        "valor_maringa": p[int(px), int(py)]})
    out["radar"] = quadros; out["km_por_pixel"] = round(kmpx, 2)
except Exception as e: out["radar_erro"] = repr(e)
json.dump(out, open("lab/sondagem_agora.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
