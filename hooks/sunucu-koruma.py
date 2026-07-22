#!/usr/bin/env python3
"""PreToolUse kancasi: Musteri sunucusu korumasi.

Sunucuda birden cok musterinin sitesi barinir. Bu kanca, calisma izni
verilmemis bir dizine dokunulmasini engeller.

Izinli dizinler artik bu dosyada sabit degil - references/sunucu-haritasi.json
icinden okunur. Yeni proje eklemek icin haritayi guncellemek yeterlidir.

Gelistirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    import gerekce
    import sunucu_harita
else:
    gerekce = None
    sunucu_harita = None

UZAK_ERISIM = re.compile(r"\b(ssh|scp|sftp|rsync)\b", re.IGNORECASE)


def _dizin_adaylari(komut, korunan_kokler):
    """Komut icinde gecen, korunan kok altindaki yollari topla."""
    bulunanlar = []
    for kok in korunan_kokler:
        for eslesme in re.finditer(re.escape(kok) + r"[^\s'\"]*", komut):
            bulunanlar.append(eslesme.group(0))
    return bulunanlar


def kontrol_et(komut):
    if not komut or not UZAK_ERISIM.search(komut):
        return None

    # Komut haritadaki sunuculardan birine mi gidiyor?
    hedef = None
    for adres in sunucu_harita.adresler():
        if adres and adres in komut:
            hedef = sunucu_harita.sunucu_bul(adres)
            break

    if hedef is None:
        return None

    korunan_kokler = sunucu_harita.korunan_kokler()
    adaylar = _dizin_adaylari(komut, korunan_kokler)

    if not adaylar:
        return None

    izinliler = sunucu_harita.izinli_dizinler(hedef)

    for aday in adaylar:
        if any(aday.startswith(izinli) for izinli in izinliler):
            continue

        # Bu dizin haritada baska bir projeye mi ait?
        _, baska_proje = sunucu_harita.proje_bul(aday, hedef)
        sahip = f"\nBu dizin '{baska_proje['ad']}' projesine ait." if baska_proje else ""

        proje_listesi = "\n".join(
            f"  {p.get('ad')}  →  {p.get('dizin')}"
            for p in hedef.get("projeler", [])
        ) or "  (haritada kayıtlı proje yok)"

        return gerekce.engelle(
            "Müşteri sunucusu koruması",
            komut,
            f"Bu komut '{aday}' dizinine erişiyor.\n"
            f"Bu dizin, çalışma izni verilen alanların dışında.{sahip}\n"
            "Kural: Sunucuda yalnız kendi proje dizininde çalışılır, "
            "diğer müşterilerin sitelerine dokunulmaz.",
            [
                "Komutu izinli bir dizine yönlendir.",
                "Gerçekten bu proje üzerinde çalışılacaksa önce haritaya ekle: "
                "references/sunucu-haritasi.json",
            ],
            f"Sunucu: {hedef.get('ad')} ({hedef.get('adres')})\n"
            f"Haritadaki projeler:\n{proje_listesi}\n"
            f"Ortak izinli dizinler: {', '.join(hedef.get('ortak_izinli_dizinler', [])) or '-'}",
        )

    return None


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR:
        print(json.dumps({
            "systemMessage": "Sunucu koruma kancasi: ortak betikler bulunamadi, kontrol atlandi."
        }))
        return

    if girdi.get("tool_name", "") != "Bash":
        print(json.dumps({}))
        return

    sonuc = kontrol_et(girdi.get("tool_input", {}).get("command", ""))
    print(json.dumps(sonuc if sonuc else {}))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Sunucu koruma kancasi hatasi: {hata}"}))
    sys.exit(0)
