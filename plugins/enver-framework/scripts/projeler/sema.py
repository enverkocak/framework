#!/usr/bin/env python3
"""Görsel sistem şeması - hangi projede ne çalışıyor, neye bağlı.

Bütün projeleri ve aralarındaki bağlantıları tek sayfada gösterir.
Kutular projeler, oklar aralarındaki veri akışı. Bir kutuya tıklayınca
o projenin ayrıntısı yanda açılır: ne işe yarıyor, hangi sunucuda,
hangi veritabanıyla, içinde neler çalışıyor.

Çıktı tek bir dosyadır; dışarıdan hiçbir şey yüklemez, çevrimdışı açılır.

Yerleşim, bağlantı yönüne göre katmanlanır: kimseden veri almayan
projeler solda, onlardan besleneler sağda. Böylece akış soldan sağa okunur.

Komutlar:
    uret     Şemayı üret
    ozet     Şemayı metin olarak özetle

Geliştirici: Enver KOCAK
"""

import argparse
import html
import json
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import kayit  # noqa: E402
import proje  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Kutu ölçüleri
KUTU_GENISLIK = 220
KUTU_YUKSEKLIK = 88
YATAY_ARALIK = 130
DIKEY_ARALIK = 34
KENAR_BOSLUK = 40

DURUM_RENKLERI = {
    "canlida": "#2e7d5b",
    "gelistirmede": "#2f6f9f",
    "yarim": "#a86a1f",
    "beklemede": "#6b6b73",
    "bitti": "#4a5568",
    "arsiv": "#5a5a60",
}


def projeleri_topla():
    """Kayıtlı bütün projeleri tanımlarıyla birlikte getir."""
    veri = kayit.kayit_oku()
    sonuc = {}

    for ad, kayit_bilgisi in veri.get("projeler", {}).items():
        tanim = kayit.tanim_getir(kayit_bilgisi)

        if tanim is None:
            tanim = {"ad": ad, "durum": "beklemede", "tanimsiz": True}

        tanim.setdefault("ad", ad)
        tanim["yerel_yol"] = kayit_bilgisi.get("yol", "")
        sonuc[ad] = tanim

    return sonuc


def baglanti_listesi(projeler):
    """Projeler arası bağlantıları çıkar."""
    baglantilar = []

    for ad, tanim in projeler.items():
        for bag in tanim.get("baglantilar", []):
            hedef = bag.get("hedef")
            if not hedef:
                continue
            baglantilar.append({
                "kaynak": ad,
                "hedef": hedef,
                "tur": bag.get("tur", ""),
                "aciklama": bag.get("aciklama", ""),
                "eksik": hedef not in projeler,
            })

    return baglantilar


def katmanla(projeler, baglantilar):
    """Bağlantı yönüne göre katman hesapla.

    Kimseden veri almayan proje 0. katmanda; ondan beslenen 1. katmanda.
    Döngü varsa katman büyümesi durdurulur, sonsuz döngüye girilmez.
    """
    gelen = {ad: set() for ad in projeler}

    for bag in baglantilar:
        if bag["eksik"]:
            continue
        gelen[bag["hedef"]].add(bag["kaynak"])

    katman = {ad: 0 for ad in projeler}

    for _ in range(len(projeler)):
        degisti = False
        for ad in projeler:
            if not gelen[ad]:
                continue
            yeni = max(katman[kaynak] for kaynak in gelen[ad]) + 1
            if yeni > katman[ad]:
                katman[ad] = yeni
                degisti = True
        if not degisti:
            break

    return katman


def yerlesim(projeler, baglantilar):
    """Her projeye ekran konumu ver."""
    katman = katmanla(projeler, baglantilar)

    # Bağlantısı olanlar ile olmayanlar ayrı toplanır
    bagli = set()
    for bag in baglantilar:
        bagli.add(bag["kaynak"])
        if not bag["eksik"]:
            bagli.add(bag["hedef"])

    bagimsiz = sorted(ad for ad in projeler if ad not in bagli)

    sutunlar = {}
    for ad in sorted(bagli):
        sutunlar.setdefault(katman[ad], []).append(ad)

    konumlar = {}

    for sutun_no in sorted(sutunlar):
        x = KENAR_BOSLUK + sutun_no * (KUTU_GENISLIK + YATAY_ARALIK)
        for sira, ad in enumerate(sutunlar[sutun_no]):
            y = KENAR_BOSLUK + sira * (KUTU_YUKSEKLIK + DIKEY_ARALIK)
            konumlar[ad] = {"x": x, "y": y, "bagimsiz": False}

    # Bağımsız projeler alta, ızgara halinde
    if konumlar:
        alt_baslangic = max(k["y"] for k in konumlar.values()) + KUTU_YUKSEKLIK + 90
    else:
        alt_baslangic = KENAR_BOSLUK

    sutun_sayisi = 4
    for sira, ad in enumerate(bagimsiz):
        satir, sutun = divmod(sira, sutun_sayisi)
        konumlar[ad] = {
            "x": KENAR_BOSLUK + sutun * (KUTU_GENISLIK + 50),
            "y": alt_baslangic + satir * (KUTU_YUKSEKLIK + DIKEY_ARALIK),
            "bagimsiz": True,
        }

    return konumlar, bool(bagimsiz), alt_baslangic


def _kacir(metin):
    return html.escape(str(metin or ""), quote=True)


def kutu_ciz(ad, tanim, konum):
    durum = tanim.get("durum", "beklemede")
    renk = DURUM_RENKLERI.get(durum, "#6b6b73")

    x, y = konum["x"], konum["y"]
    baslik = ad if len(ad) <= 26 else ad[:24] + "…"
    gorev = tanim.get("gorev") or tanim.get("aciklama") or ""
    gorev_kisa = gorev if len(gorev) <= 34 else gorev[:32] + "…"

    servis_sayisi = len(tanim.get("servisler", []))
    alt_bilgi = f"{servis_sayisi} servis" if servis_sayisi else ""

    if tanim.get("tanimsiz"):
        alt_bilgi = "tanım yok"

    return f"""
  <g class="dugum" data-ad="{_kacir(ad)}" transform="translate({x},{y})">
    <rect class="kutu" width="{KUTU_GENISLIK}" height="{KUTU_YUKSEKLIK}" rx="10"/>
    <rect class="serit" width="5" height="{KUTU_YUKSEKLIK}" rx="2.5" fill="{renk}"/>
    <text class="ad" x="18" y="26">{_kacir(baslik)}</text>
    <text class="gorev" x="18" y="48">{_kacir(gorev_kisa)}</text>
    <text class="durum" x="18" y="70" fill="{renk}">{_kacir(proje.DURUM_ETIKETLERI.get(durum, durum))}</text>
    <text class="alt" x="{KUTU_GENISLIK - 16}" y="70" text-anchor="end">{_kacir(alt_bilgi)}</text>
  </g>"""


def ok_ciz(bag, konumlar):
    kaynak = konumlar.get(bag["kaynak"])
    hedef = konumlar.get(bag["hedef"])

    if not kaynak or not hedef:
        return ""

    x1 = kaynak["x"] + KUTU_GENISLIK
    y1 = kaynak["y"] + KUTU_YUKSEKLIK / 2
    x2 = hedef["x"]
    y2 = hedef["y"] + KUTU_YUKSEKLIK / 2

    # Hedef solda kalıyorsa kutunun altından dolaş
    if x2 < x1:
        x1 = kaynak["x"] + KUTU_GENISLIK / 2
        y1 = kaynak["y"] + KUTU_YUKSEKLIK
        x2 = hedef["x"] + KUTU_GENISLIK / 2
        y2 = hedef["y"] + KUTU_YUKSEKLIK
        orta = max(y1, y2) + 40
        yol = f"M {x1} {y1} C {x1} {orta}, {x2} {orta}, {x2} {y2}"
    else:
        kavis = max(50, (x2 - x1) / 2)
        yol = f"M {x1} {y1} C {x1 + kavis} {y1}, {x2 - kavis} {y2}, {x2} {y2}"

    etiket = bag.get("tur") or ""
    baslik = f"{bag['kaynak']} → {bag['hedef']}"
    if bag.get("aciklama"):
        baslik += f": {bag['aciklama']}"

    etiket_ogesi = ""
    if etiket:
        ox, oy = (x1 + x2) / 2, (y1 + y2) / 2 - 8
        etiket_ogesi = f'<text class="ok-etiket" x="{ox}" y="{oy}" text-anchor="middle">{_kacir(etiket)}</text>'

    return f"""
  <g class="ok">
    <title>{_kacir(baslik)}</title>
    <path d="{yol}" marker-end="url(#okucu)"/>
    {etiket_ogesi}
  </g>"""


def html_uret(projeler, baglantilar, konumlar, bagimsiz_var, ayirac_y):
    if konumlar:
        genislik = max(k["x"] for k in konumlar.values()) + KUTU_GENISLIK + KENAR_BOSLUK
        yukseklik = max(k["y"] for k in konumlar.values()) + KUTU_YUKSEKLIK + KENAR_BOSLUK
    else:
        genislik, yukseklik = 800, 400

    kutular = "".join(kutu_ciz(ad, projeler[ad], konumlar[ad]) for ad in sorted(konumlar))
    oklar = "".join(ok_ciz(bag, konumlar) for bag in baglantilar)

    ayirac = ""
    if bagimsiz_var:
        ayirac = f"""
  <line class="ayirac" x1="{KENAR_BOSLUK}" y1="{ayirac_y - 46}" x2="{genislik - KENAR_BOSLUK}" y2="{ayirac_y - 46}"/>
  <text class="ayirac-yazi" x="{KENAR_BOSLUK}" y="{ayirac_y - 56}">Bağlantısı tanımlanmamış projeler</text>"""

    veri = json.dumps(projeler, ensure_ascii=False)

    durum_gostergesi = "".join(
        f'<span class="rozet"><i style="background:{renk}"></i>{_kacir(proje.DURUM_ETIKETLERI.get(durum, durum))}</span>'
        for durum, renk in DURUM_RENKLERI.items()
    )

    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sistem Şeması</title>
<style>
  :root {{
    --zemin: #f6f7f9; --kart: #ffffff; --yazi: #1c1f24; --soluk: #62676e;
    --cizgi: #d9dde3; --vurgu: #2f6f9f; --golge: 0 1px 3px rgba(0,0,0,.08);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --zemin: #14161a; --kart: #1c1f25; --yazi: #e8eaed; --soluk: #9aa0a8;
      --cizgi: #2c3138; --vurgu: #5fa8d8; --golge: 0 1px 3px rgba(0,0,0,.4);
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--zemin); color: var(--yazi);
    font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  header {{
    padding: 18px 24px; border-bottom: 1px solid var(--cizgi);
    background: var(--kart); position: sticky; top: 0; z-index: 5;
  }}
  h1 {{ margin: 0 0 4px; font-size: 18px; font-weight: 600; }}
  .altyazi {{ color: var(--soluk); font-size: 13px; }}
  .rozetler {{ margin-top: 10px; display: flex; flex-wrap: wrap; gap: 14px; }}
  .rozet {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--soluk); }}
  .rozet i {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}

  .govde {{ display: flex; align-items: flex-start; }}
  .tuval {{ flex: 1; overflow: auto; padding: 20px; }}
  svg {{ display: block; }}

  .kutu {{ fill: var(--kart); stroke: var(--cizgi); stroke-width: 1; filter: drop-shadow(var(--golge)); }}
  .dugum {{ cursor: pointer; }}
  .dugum:hover .kutu {{ stroke: var(--vurgu); stroke-width: 2; }}
  .dugum.secili .kutu {{ stroke: var(--vurgu); stroke-width: 2.5; }}
  .ad {{ font-size: 14px; font-weight: 600; fill: var(--yazi); }}
  .gorev {{ font-size: 11.5px; fill: var(--soluk); }}
  .durum {{ font-size: 11px; font-weight: 600; }}
  .alt {{ font-size: 11px; fill: var(--soluk); }}

  .ok path {{ fill: none; stroke: var(--cizgi); stroke-width: 1.8; }}
  .ok:hover path {{ stroke: var(--vurgu); stroke-width: 2.4; }}
  .ok-etiket {{ font-size: 10.5px; fill: var(--soluk); }}
  .ayirac {{ stroke: var(--cizgi); stroke-dasharray: 4 4; }}
  .ayirac-yazi {{ font-size: 12px; fill: var(--soluk); }}

  aside {{
    width: 330px; flex-shrink: 0; padding: 20px; background: var(--kart);
    border-left: 1px solid var(--cizgi); min-height: calc(100vh - 90px);
    position: sticky; top: 90px; overflow-y: auto; max-height: calc(100vh - 90px);
  }}
  aside h2 {{ margin: 0 0 4px; font-size: 16px; }}
  aside .bos {{ color: var(--soluk); font-size: 13px; }}
  aside dl {{ margin: 14px 0 0; display: grid; grid-template-columns: auto 1fr; gap: 6px 12px; font-size: 13px; }}
  aside dt {{ color: var(--soluk); }}
  aside dd {{ margin: 0; word-break: break-word; }}
  aside h3 {{ margin: 18px 0 6px; font-size: 13px; color: var(--soluk); font-weight: 600; }}
  aside ul {{ margin: 0; padding-left: 18px; font-size: 13px; }}
  aside li {{ margin-bottom: 4px; }}

  @media (max-width: 900px) {{
    .govde {{ flex-direction: column; }}
    aside {{ width: 100%; position: static; max-height: none; min-height: 0;
             border-left: none; border-top: 1px solid var(--cizgi); }}
  }}
</style>
</head>
<body>
<header>
  <h1>Sistem Şeması</h1>
  <div class="altyazi">{len(projeler)} proje · {len(baglantilar)} bağlantı · Bir kutuya tıklayınca ayrıntısı yanda açılır</div>
  <div class="rozetler">{durum_gostergesi}</div>
</header>

<div class="govde">
  <div class="tuval">
    <svg width="{genislik}" height="{yukseklik}" viewBox="0 0 {genislik} {yukseklik}">
      <defs>
        <marker id="okucu" viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" opacity="0.45"/>
        </marker>
      </defs>
      {ayirac}
      {oklar}
      {kutular}
    </svg>
  </div>

  <aside id="panel">
    <h2>Ayrıntı</h2>
    <p class="bos">Soldaki kutulardan birine tıkla.</p>
  </aside>
</div>

<script>
const PROJELER = {veri};

const DURUM_ADLARI = {{
  gelistirmede: "Geliştirmede", yarim: "Yarım kaldı", canlida: "Canlıda",
  beklemede: "Beklemede", bitti: "Bitti", arsiv: "Arşivde"
}};

function kacir(s) {{
  return String(s == null ? "" : s).replace(/[&<>"]/g, c =>
    ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }})[c]);
}}

function satir(etiket, deger) {{
  if (!deger) return "";
  const metin = Array.isArray(deger) ? deger.join(", ") : deger;
  return `<dt>${{kacir(etiket)}}</dt><dd>${{kacir(metin)}}</dd>`;
}}

function goster(ad) {{
  const t = PROJELER[ad];
  const panel = document.getElementById("panel");
  if (!t) return;

  let icerik = `<h2>${{kacir(t.ad || ad)}}</h2>`;

  if (t.tanimsiz) {{
    icerik += `<p class="bos">Bu projenin tanım dosyası yok.<br>
      Ayrıntı görünmesi için o projede tanım oluşturulmalı.</p>
      <dl>${{satir("Yol", t.yerel_yol)}}</dl>`;
    panel.innerHTML = icerik;
    return;
  }}

  if (t.aciklama) icerik += `<p class="bos">${{kacir(t.aciklama)}}</p>`;

  icerik += "<dl>" +
    satir("Görev", t.gorev) +
    satir("Durum", DURUM_ADLARI[t.durum] || t.durum) +
    satir("Müşteri", t.musteri) +
    satir("Sunucu", t.sunucu) +
    satir("Dizin", t.dizin) +
    satir("Alan adı", t.alan_adi) +
    satir("Veritabanı", t.veritabani) +
    satir("Teknolojiler", t.teknolojiler) +
    satir("Yol", t.yerel_yol) +
    "</dl>";

  if (t.kasa_anahtari) {{
    icerik += `<h3>Gizli bilgi</h3><ul><li>Kasada: ${{kacir(t.kasa_anahtari)}}
      <br><span style="color:var(--soluk)">Okumak için kasa açılmalı.</span></li></ul>`;
  }}

  if (t.servisler && t.servisler.length) {{
    icerik += "<h3>Neler çalışıyor</h3><ul>";
    for (const s of t.servisler) {{
      icerik += `<li><b>${{kacir(s.ad)}}</b>${{s.tur ? " (" + kacir(s.tur) + ")" : ""}}
        ${{s.gorev || s.aciklama ? " — " + kacir(s.gorev || s.aciklama) : ""}}</li>`;
    }}
    icerik += "</ul>";
  }}

  if (t.baglantilar && t.baglantilar.length) {{
    icerik += "<h3>Bağlı olduğu projeler</h3><ul>";
    for (const b of t.baglantilar) {{
      icerik += `<li><b>${{kacir(b.hedef)}}</b>${{b.tur ? " (" + kacir(b.tur) + ")" : ""}}
        ${{b.aciklama ? " — " + kacir(b.aciklama) : ""}}</li>`;
    }}
    icerik += "</ul>";
  }}

  if (t.tarihler && Object.keys(t.tarihler).length) {{
    icerik += "<h3>Tarihler</h3><ul>";
    for (const [k, v] of Object.entries(t.tarihler)) {{
      icerik += `<li>${{kacir(k)}}: ${{kacir(v)}}</li>`;
    }}
    icerik += "</ul>";
  }}

  if (t.notlar) icerik += `<h3>Notlar</h3><p class="bos">${{kacir(t.notlar)}}</p>`;

  panel.innerHTML = icerik;
}}

document.querySelectorAll(".dugum").forEach(dugum => {{
  dugum.addEventListener("click", () => {{
    document.querySelectorAll(".dugum").forEach(d => d.classList.remove("secili"));
    dugum.classList.add("secili");
    goster(dugum.dataset.ad);
  }});
}});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- komutlar

def komut_uret(args):
    projeler = projeleri_topla()

    if not projeler:
        print("Kayıtlı proje yok. Önce: python kayit.py tara")
        return 1

    baglantilar = baglanti_listesi(projeler)
    konumlar, bagimsiz_var, ayirac_y = yerlesim(projeler, baglantilar)

    icerik = html_uret(projeler, baglantilar, konumlar, bagimsiz_var, ayirac_y)

    hedef = Path(args.hedef) if args.hedef else Path(yollar.proje_kok()) / "_calisma" / "sistem-semasi.html"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(icerik, encoding="utf-8")

    tanimli = sum(1 for t in projeler.values() if not t.get("tanimsiz"))

    print(f"Şema üretildi: {hedef}")
    print(f"  {len(projeler)} proje ({tanimli} tanesi tanımlı)")
    print(f"  {len(baglantilar)} bağlantı")

    eksik = [b for b in baglantilar if b["eksik"]]
    if eksik:
        print()
        print(f"  {len(eksik)} bağlantının hedefi kayıtlı değil:")
        for bag in eksik[:5]:
            print(f"    {bag['kaynak']} → {bag['hedef']}")

    tanimsiz = len(projeler) - tanimli
    if tanimsiz:
        print()
        print(f"  {tanimsiz} projenin tanımı yok; şemada ayrıntısı görünmüyor.")

    if args.ac:
        webbrowser.open(hedef.resolve().as_uri())

    return 0


def komut_ozet(args):
    projeler = projeleri_topla()
    baglantilar = baglanti_listesi(projeler)
    katman = katmanla(projeler, baglantilar)

    print(f"SİSTEM ŞEMASI ÖZETİ")
    print("=" * 60)
    print(f"{len(projeler)} proje, {len(baglantilar)} bağlantı")
    print()

    for ad in sorted(projeler, key=lambda a: (katman[a], a)):
        tanim = projeler[ad]
        durum = proje.DURUM_ETIKETLERI.get(tanim.get("durum"), tanim.get("durum", "-"))
        gorev = tanim.get("gorev") or tanim.get("aciklama") or "-"

        print(f"  [{katman[ad]}] {ad}  ({durum})")
        print(f"      {gorev[:70]}")

        for bag in tanim.get("baglantilar", []):
            isaret = "?" if bag.get("hedef") not in projeler else "→"
            print(f"      {isaret} {bag.get('hedef')}  {bag.get('aciklama', '')}")
        print()

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Görsel sistem şeması")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("uret", help="Şemayı üret")
    p.add_argument("--hedef")
    p.add_argument("--ac", action="store_true", help="Üretince tarayıcıda aç")
    p.set_defaults(islev=komut_uret)

    p = alt.add_parser("ozet", help="Metin özeti")
    p.set_defaults(islev=komut_ozet)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
