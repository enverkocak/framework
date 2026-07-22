#!/usr/bin/env python3
"""Belgelerde geçen dosya yollarının gerçekten var olup olmadığını denetler.

Neden gerekli:
    CLAUDE.md kurulumda ~/.claude/CLAUDE.md konumuna kopyalanır ve HER
    projede yüklenir. İçinde geçen göreli bir yol, o an hangi projede
    çalışılıyorsa ona göre çözülür - yani yanlış yeri gösterir.
    Kurulu düzende doğru yol '~/.claude/plugins/...' biçimindedir.

    Bu ayrımı gözle yakalamak zor: yol depo içinde doğru görünür,
    kurulu düzende bozuktur.

Kullanım:
    python yol-denetim.py [proje-kökü]

Geliştirici: Enver KOCAK
"""

import re
import sys
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]

# Kurulumda ~/.claude altına kopyalanan, yani her projede yüklenen belgeler.
# Bunlarda göreli yol kullanılamaz.
KURULAN_BELGELER = ["CLAUDE.md", "CLAUDE.ornek.md"]

# Depo içinde kalan, kök dizine göre okunan belgeler.
DEPODA_KALAN = [
    "README.md", "README.ornek.md",
    "KULLANIM-KILAVUZU.md", "KURULUM-KILAVUZU.md",
]

# DEĞİŞİKLİKLER.md denetlenmez: sürüm geçmişi, o gün var olan dosyaları
# anlatır. Silinmiş ya da adı değişmiş bir dosyayı anması doğru davranıştır.

# Her projenin kendi içinde oluşan klasörler. CLAUDE.md'de bunların
# göreli yazılması DOĞRUDUR - çerçeve dosyası değil, çalışılan projenin
# kendi klasörleridir. Ayrıca kullanılmadan önce var olmayabilirler.
PROJE_KLASORLERI = ("_calisma/", "_arsiv/", "gunluk/", "hafiza/",
                    "kasa/", "vault/", ".claude/")

# Ters tırnak içindeki yol benzeri parçalar. Uzantı taşıyan ya da
# bölü içeren, boşluksuz diziler yol sayılır.
YOL_DESENI = re.compile(r"`([^`\n]+)`")

# Yol sayılmayacaklar: komutlar, değişkenler, örnek değerler
ATLA = re.compile(
    r"^(/|\$|--|~$)"           # egik cizgiyle baslayan komut, bayrak
    r"|^[a-z]+ [a-z]"          # 'git push' gibi komut satirlari
    r"|^\d"                    # sayi
    r"|^(true|false|null)$"
)


def yol_mu(parca):
    if ATLA.search(parca):
        return False
    if parca.startswith(PROJE_KLASORLERI):
        return False
    if " " in parca:
        return False
    # Sadece klasör ayracı taşıyanlar yol sayılır. Tek başına bir dosya
    # adı (CLAUDE.md gibi) yol değil, Addır; nereye bakılacağını
    # söylemez ve denetlenecek bir hedefi yoktur.
    return "/" in parca


def denetle(bagil_belge, kurulan):
    """Bir belgedeki yolları denetler. kurulan=True ise ~ zorunludur."""
    belge = KOK / bagil_belge
    if not belge.is_file():
        return []

    bulgular = []
    for satir_no, satir in enumerate(belge.read_text(encoding="utf-8").splitlines(), 1):
        for parca in YOL_DESENI.findall(satir):
            if not yol_mu(parca):
                continue

            ev_yolu = parca.startswith("~/.claude/")

            if kurulan:
                # Kurulu belgede göreli yol yanlıştır.
                if not ev_yolu and not parca.startswith("~"):
                    # Depoda karşılığı varsa bu gerçek bir yol demektir;
                    # olmayan bir şey ise zaten başka bir bulgudur.
                    if (KOK / parca).exists():
                        bulgular.append((
                            satir_no, parca,
                            "göreli yol - kurulu düzende yanlış yeri gösterir",
                            "~/.claude/" + parca,
                        ))
                    continue
                # ~/.claude/ ile başlayan yolun kurulu karşılığı
                # depoda hangi dosyaya denk geliyorsa o var olmalı.
                if ev_yolu:
                    kalan = parca[len("~/.claude/"):]
                    # vault, bilgi, şablonlar depo kökünde de aynı adla durur
                    if not (KOK / kalan).exists() and not (KOK / kalan).parent.exists():
                        bulgular.append((
                            satir_no, parca,
                            "kurulu düzende karşılığı bulunamadı", None,
                        ))
            else:
                if ev_yolu or parca.startswith("~"):
                    continue
                if not (KOK / parca).exists():
                    bulgular.append((
                        satir_no, parca, "depoda böyle bir yol yok", None,
                    ))

    return bulgular


def main():
    toplam = 0
    print()
    print("  BELGE YOL DENETİMİ")
    print("  " + "-" * 62)

    for belge in KURULAN_BELGELER:
        bulgular = denetle(belge, kurulan=True)
        toplam += len(bulgular)
        if bulgular:
            print(f"\n  {belge} (kurulumda ~/.claude altina gider)")
            for satir_no, parca, neden, oneri in bulgular:
                print(f"    satır {satir_no}: {parca}")
                print(f"      {neden}")
                if oneri:
                    print(f"      olması gereken: {oneri}")

    for belge in DEPODA_KALAN:
        bulgular = denetle(belge, kurulan=False)
        toplam += len(bulgular)
        if bulgular:
            print(f"\n  {belge} (depoda kalir)")
            for satir_no, parca, neden, _ in bulgular:
                print(f"    satır {satir_no}: {parca}")
                print(f"      {neden}")

    print()
    if toplam:
        print(f"  Yol denetimi: {toplam} sorunlu yol")
        return 1

    print("  Yol denetimi: bütün yollar doğru")
    return 0


if __name__ == "__main__":
    sys.exit(main())
