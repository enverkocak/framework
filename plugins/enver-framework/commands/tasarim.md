---
description: Ozgun tasarim - kimlik uretimi, ilham kaynaklari, kalip denetimi ve iz imzasi
---

# Tasarım

**Kural:** İki proje aynı görünmez. Bakan kişi "bunlar aynı yerden çıkmış" diyemez.

## Komutlar

```bash
T="${CLAUDE_PLUGIN_ROOT}/scripts/tasarim"

python "$T/kimlik.py" uret                 # bu projeye görsel kimlik üret
python "$T/kimlik.py" css --hedef stil.css # kimliği CSS değişkenlerine çevir
python "$T/kimlik.py" liste                # kullanılmış bütün kimlikler
python "$T/kimlik.py" denetle              # okunabilirlik ölçütleri

python "$T/ilham.py" yazitipi sec --karakter luks   # yazı tipi eşleşmesi öner
python "$T/ilham.py" yazitipi liste                  # katalog
python "$T/ilham.py" site <adres>                    # örnek siteyi çözümle

python "$T/kalip-denetim.py" tara <yol>    # şablon işaretlerini ara
python "$T/kalip-denetim.py" kurallar      # aranan kalıplar

python "$T/imza.py" ayarla --sirket "<ad>" # iz kimliğini belirle
python "$T/imza.py" uret                   # imza içeriğini üret
python "$T/imza.py" denetle                # ön planda mı

python "$T/cihaz.py" liste                 # cihaz sınıfları
python "$T/cihaz.py" css --hedef cihaz.css # cihaz katmanı üret
python "$T/cihaz.py" iskelet               # sayfa iskeleti
python "$T/cihaz.py" denetle <yol>         # cihaz uyumunu ölç
```

## Cihaza göre tasarım

Beş sınıf: **mobil · büyük mobil · tablet · web · masaüstü**

Tek düzeni küçültüp büyütmek yeterli değil — her sınıfın kendi yerleşimi,
kendi dokunma hedefleri, kendi okuma genişliği var.

Ekran genişliği de tek ölçüt değil: dokunmatik mı, hareket azaltma isteniyor
mu, ekran yoğunluğu ne — hepsine bakılıyor.

---

## Yeni projede tasarım akışı

### 1. Brifing al (kod yazmadan önce)

Kullanıcıya **sor**, varsayma:

- **Sektör ve iş** — ne satıyor, ne yapıyor?
- **Hedef kitle** — kim kullanacak? (yaş, teknik düzey, kurumsal mı bireysel mi)
- **Duygu** — hangisi: ciddi · samimi · lüks · teknik · hızlı · sakin · iddialı
- **Beğendiği örnek siteler** — 2-3 adres
- **Sevmediği** — nelerden kaçınmalı
- **Zorunluluklar** — mevcut logo, kurumsal renk, marka kuralı var mı

### 2. Örnek siteleri çözümle

```bash
python "$T/ilham.py" site <adres>
```

Çıkan şey renk kodu değil **yön**dür: sıcak mı soğuk, doygun mu sönük,
ciddi mi samimi, yoğun mu ferah.

**Kopyalama.** Kopya hem etik değildir hem de zaten aynılaşmaya götürür.

### 3. Kimlik üret

```bash
python "$T/kimlik.py" uret
```

Üretilen kimlik daha önce kullanılmış kimliklerden **uzak tutulur**;
ana ton en az 28 derece farklı olur. Bütün renk çiftleri okunabilirlik
açısından denetlenir.

### 4. Yazı tipini seç

```bash
python "$T/ilham.py" yazitipi sec --karakter <karakter>
```

Karakterler: editoryal · geometrik · humanist · dar · teknik · luks ·
yumusak · keskin · resmi · sicak

### 5. Kimliği koda dök

```bash
python "$T/kimlik.py" css --hedef <proje>/stil/kimlik.css
```

Bundan sonra **renk ve ölçü değerleri elle yazılmaz**, hep değişkenden gelir.
Böylece tutarlılık kendiliğinden korunur.

### 6. Teslimden önce denetle

```bash
python "$T/kalip-denetim.py" tara <proje>
python "$T/imza.py" denetle
```

Yüksek ağırlıklı bulgu kalmamalı.

---

## Kalıp denetimi ne arar

Şablon hissi veren işaretler:

| Ağırlık | Örnek |
|---------|-------|
| Yüksek | Herkesin kullandığı mor-mavi geçiş · her yerde aynı varsayılan yazı tipi · yer tutucu metin · İngilizce arayüz · üretici etiketi · şablondan kalma yorum |
| Orta | Üç kartlık özellik bölümü · ortalanmış başlık + iki düğme · emoji ikonlar · çalışmayan bağlantılar |
| Düşük | Tek köşe değeri · her yerde aynı gölge · elle yazılmış yıl |

---

## İz kimliği

Enver'in kuralı: **her projede farklı olabilir, detaylı olacak, ön planda görünmeyecek.**

Beş biçim var; her projeye en az kullanılmış olanlardan biri verilir:
kaynak yorumu · meta etiketleri · humans.txt · yapısal veri · ince alt bilgi.

**Şirket bilgisi projeye göre değişebilir** — her projede ayrı verilir:

```bash
python "$T/imza.py" ayarla --sirket "<projeye uygun ad>"
```

---

## Kesin kurallar

- **Araç izi bırakılmaz.** Kodda, yorumda, meta etikette, commit mesajında,
  dosya adında hiçbir üretim aracı görünmez.
- **Arayüz Türkçe.** Tam Türkçe karakterle: ö, ç, ü, ğ, ı, ş, İ
- **Erişilebilirlik ölçülür.** Karşıtlık oranı denetlenmeden renk kullanılmaz.
- **Açık ve koyu tema.** İkisi de çalışacak.
- **Mobil uyum.** Yatay kaydırma olmayacak.

## İlgili

- `/projeler` — proje tanımları
- `/index` — bütün komutlar
