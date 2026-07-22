#!/usr/bin/env python3
"""Türkçe gerekçe üreteci - bütün korumalar aynı biçimde konuşur.

Kural (E15/E16):
  - Bir işlem engellendiğinde NEDEN engellendiği Türkçe yazılır.
  - İzin istenirken NE İÇİN istendiği Türkçe yazılır.
  - Kullanıcı ne onayladığını bilmeden onay vermez.

Her gerekçe dört parçadan oluşur:
  BAŞLIK        ne oldu
  NE YAPILACAKTI  engellenen işlem tam olarak neydi
  NEDEN         hangi kural devreye girdi
  NASIL DÜZELTİLİR  kullanıcının önünde duran seçenekler

Geliştirici: Enver KOCAK
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import metin  # noqa: E402

CIZGI = "-" * 52


def _kisalt(deger, sinir=200):
    """Uzun komutları okunur uzunlukta tut."""
    deger = " ".join(str(deger).split())
    if len(deger) <= sinir:
        return deger
    return deger[:sinir] + " ..."


def olustur(baslik, ne_yapilacakti, neden, nasil_duzeltilir=None, ek_bilgi=None):
    """İnsan okuyacak gerekçe metnini üret."""
    satirlar = [baslik, CIZGI, ""]

    if ne_yapilacakti:
        satirlar += [f"{metin.al('korumalar.ne_yapilacak')}:", f"  {_kisalt(ne_yapilacakti)}", ""]

    satirlar += [f"{metin.al('korumalar.neden')}:"]
    satirlar += [f"  {satir}" for satir in str(neden).strip().splitlines()]
    satirlar.append("")

    if ek_bilgi:
        satirlar += [f"  {satir}" for satir in str(ek_bilgi).strip().splitlines()]
        satirlar.append("")

    if nasil_duzeltilir:
        satirlar.append(f"{metin.al('korumalar.nasil_duzeltilir')}:")
        if isinstance(nasil_duzeltilir, (list, tuple)):
            satirlar += [f"  {sira}. {secenek}" for sira, secenek in enumerate(nasil_duzeltilir, 1)]
        else:
            satirlar += [f"  {satir}" for satir in str(nasil_duzeltilir).strip().splitlines()]
        satirlar.append("")

    return "\n".join(satirlar).rstrip()


def engelle(baslik, ne_yapilacakti, neden, nasil_duzeltilir=None, ek_bilgi=None):
    """İşlemi tamamen reddet. Kullanıcı onay veremez, önce düzeltmesi gerekir."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": olustur(
                f"{metin.al('korumalar.engellendi')} - {baslik}",
                ne_yapilacakti, neden, nasil_duzeltilir, ek_bilgi,
            ),
        }
    }


def onay_iste(baslik, ne_yapilacakti, neden, nasil_duzeltilir=None, ek_bilgi=None):
    """Kullanıcıdan açık onay iste. Ne için izin istendiği yazılır (E16)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": olustur(
                f"{metin.al('korumalar.izin_gerekli')} - {baslik}",
                ne_yapilacakti, neden, nasil_duzeltilir, ek_bilgi,
            ),
        }
    }


def izin_ver():
    """Karar verme, normal akışa bırak."""
    return {}


def uyar(baslik, neden, nasil_duzeltilir=None):
    """İşlem sonrası uyarı (PostToolUse). Engellemez, bilgilendirir."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": olustur(
                f"{metin.al('genel.uyari')} - {baslik}",
                None, neden, nasil_duzeltilir,
            ),
        }
    }


if __name__ == "__main__":
    import json

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ornek = engelle(
        "Silme korumasi",
        "rm -rf eski-proje/",
        "Bu komut veriyi kalıcı olarak siliyor.\nKural: Hiçbir veri silinmez, arşivlenir.",
        [
            "Arşivle: python scripts/ortak/arsiv.py eski-proje/ \"iş adı\" \"neden\"",
            "Gerçekten silinmesi gerekiyorsa dosya yöneticisinden elle sil.",
        ],
    )
    print(json.loads(json.dumps(ornek))["hookSpecificOutput"]["permissionDecisionReason"])
