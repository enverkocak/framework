---
name: ozgun-tasarim
description: 'Bir web sitesi, arayuz, sayfa, panel ya da herhangi bir gorsel yuzey tasarlanacaksa - renk secilecekse, yazi tipi belirlenecekse, duzen kurulacaksa, HTML/CSS yazilacaksa - ONCE bu beceriyi kullan. Kullanici "site yap", "sayfa tasarla", "arayuz kur", "tasarim", "renk", "yazi tipi", "sablon gibi durmasin", "ozgun olsun" derse ya da yeni bir proje baslatirsa acikca istemese bile bu beceri devreye girer. Amaci - iki projenin birbirine benzememesi ve hicbir projede uretim araci izi kalmamasi.'
---

# Özgün tasarım

Enver'in ULTRA ÖNEMLİ kuralı:

> Projelere bakanlar hemen "bu otomatik üretilmiş" diyor, çünkü tasarımlar hep aynı.
> Özgün tasarım istiyorum. Hiç kimse kodlamanın nasıl yapıldığını anlamamalı.

Bu beceri o kuralı uygulanabilir hale getirir.

## Kod yazmadan önce

**Asla varsayma, sor.** Tasarım brifingi olmadan renk seçilmez:

1. **Sektör ve iş** — ne satıyor, ne yapıyor?
2. **Hedef kitle** — kim kullanacak?
3. **Duygu** — ciddi · samimi · lüks · teknik · hızlı · sakin · iddialı
4. **Beğendiği örnekler** — 2-3 site adresi
5. **Sevmediği** — nelerden kaçınmalı
6. **Zorunluluklar** — mevcut logo, kurumsal renk

Kullanıcı "sen bir şey yap" derse bile en az **duygu** ve **sektör** sorulmalı.
Bu ikisi olmadan üretilen tasarım genel geçer olur; sorun da tam budur.

## Örnek siteyi çözümleme

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/ilham.py" site <adres>
```

Çıkan sonuç bir **yön tarifidir**, kopyalama reçetesi değil.
Renk kodlarını almak yerine şunu çıkar: sıcak mı soğuk, doygun mu sönük,
ciddi mi samimi, yoğun mu ferah, keskin mi yumuşak.

O yönü al, **özgün** bir kimlik üret.

## Kimlik üretimi

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/kimlik.py" uret
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/kimlik.py" css --hedef <proje>/stil/kimlik.css
```

Üreteç şunları garanti eder:

- Ana ton, daha önce kullanılmış kimliklerden **en az 28 derece** uzak
- Tipografi, boşluk ritmi, köşe dili, derinlik ve düzen karakteri de değişir
- Bütün renk çiftleri **okunabilirlik ölçütünü** karşılar (gövde metni 4.5:1)
- Açık ve koyu tema birlikte üretilir

## Kod yazarken

- **Renk ve ölçü değerlerini elle yazma.** Hep kimlik değişkeninden al:
  `var(--ana)`, `var(--aralik-4)`, `var(--kose-orta)`
- **Yazı tipini kataloğa sor**, akla ilk geleni kullanma:
  `ilham.py yazitipi sec --karakter <karakter>`
- **Arayüz metinleri tam Türkçe:** ö, ç, ü, ğ, ı, ş, İ
- **Değişken ve dosya adları ASCII**

## Kaçınılacak kalıplar

Bunlar tek başına bile "şablon" dedirtir:

- Mor-mavi geçiş (`#667eea` ve benzerleri)
- Her yerde tek bir varsayılan yazı tipi
- Ortalanmış başlık + altında iki düğme
- Tam üç kartlık özellik bölümü
- İkon yerine emoji
- Yer tutucu Latince metin
- İngilizce arayüz yazıları
- Hazır çerçeve bileşenlerinin hiç değiştirilmemiş hâli

## Cihaza göre tasarım (E20)

**Tek bir düzeni küçültüp büyütmek yeterli değildir.** Beş cihaz sınıfının
her birinin kendi yerleşimi, kendi dokunma hedefleri, kendi okuma genişliği olur.

```bash
C="${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/cihaz.py"

python "$C" liste                        # cihaz sınıfları ve eşikleri
python "$C" css --hedef stil/cihaz.css   # cihaz katmanı üret
python "$C" iskelet --hedef index.html   # çalışan sayfa iskeleti
python "$C" denetle <yol>                # cihaz uyumunu ölç
```

| Sınıf | Genişlik | Karakter |
|-------|----------|----------|
| Mobil | 0-479 | Tek sütun, tek elle kullanım, alt gezinme |
| Büyük mobil | 480-767 | Tek sütun ama rahat |
| Tablet | 768-1023 | İki sütun, açılır yan panel |
| Web | 1024-1439 | Çok sütun, üst gezinme, imleç odaklı |
| Masaüstü | 1440+ | Geniş ekran, okuma genişliği korunur |

**Ekran genişliği tek başına yetmez.** Ayrıca cihazın kendisi tanınır:
dokunmatik mı ince imleç mi, yatay mı dikey mi, hareket azaltma isteniyor mu,
ekran yoğunluğu ne.

1024px'lik bir dokunmatik ekran, aynı genişlikteki bir dizüstünden
**farklı davranmalı.**

## Teslimden önce

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/kalip-denetim.py" tara <proje>
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/imza.py" denetle
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/cihaz.py" denetle <proje>
```

Yüksek ağırlıklı bulgu kalmamalı.

## İz kimliği

Her projeye bir imza gömülür ama **ön planda görünmez**:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/tasarim/imza.py" ayarla --sirket "<ad>"
```

- İmza biçimi **her projede farklı** olur (beş biçimden en az kullanılanı)
- **Şirket bilgisi projeye göre değişebilir** — sabit değildir
- İmza büyük yazılmaz, kalın yazılmaz, sabit konumlanmaz

## Araç izi

Kodda, yorumda, meta etikette, commit mesajında, dosya adında hiçbir üretim
aracı görünmez. Geliştirici bilgisi her zaman **Enver KOCAK**.

Bu kural müşteri projelerinde **istisnasızdır**.
