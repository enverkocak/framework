---
description: Var olan bir projeyi derinlemesine tarar, ogrenir ve cerceveye uyarlar
argument-hint: Proje dizini (bos birakilirsa bulunulan proje)
---

# Proje Devral

Sıfırdan başlamayan, **zaten var olan** bir projeyi çerçeveye bağlar.
Önce okur, sonra öğrendiğini yazıya döker, en son onay alıp uyarlar.

`/proje-baslat` yeni proje içindir. `/kesif` sorularla ilerler.
Bu komut **koda bakarak** öğrenir.

## Kural

**Onay alınmadan tek dosya yazılmaz.** Tarama aşaması hiçbir şeye dokunmaz;
yalnız `_calisma/devralma/` altına rapor bırakır. Var olan bir dosyanın
üzerine hiçbir aşamada yazılmaz.

---

## 1. Hedefi belirle

`$ARGUMENTS` bir dizin veriyorsa o dizin, vermiyorsa bulunulan proje.

Hedef başka birinin ya da müşterinin projesiyse önce söyle: hangi dizinde
çalışılacağını tek satırla bildir, yanlış dizinse kullanıcı seni durdurur.

## 2. Mekanik tarama

```bash
D="${CLAUDE_PLUGIN_ROOT}/scripts/projeler/devral.py"

python "$D" tara --yol "<kök>"
```

Çıkan rapor: `_calisma/devralma/rapor.md`  
Ham envanter: `_calisma/devralma/envanter.json`

Raporu **oku**. Dizin haritası, geçmiş, riskler, yarım işler ve eksik
çerçeve dosyaları burada. Sonraki adımın girdisi bu.

## 3. Derin okuma - paralel ajanlar

Beş ajanı **aynı anda** başlat. Her biri `devralma-ajani` tipinde, tek
farkları rolleri:

| Rol | Neye bakar |
|-----|-----------|
| `mimari` | Katmanlar, giriş noktaları, istek akışı |
| `veri` | Veri modeli, göçler, dış servisler |
| `surec` | Kurulum, çalıştırma, yayına alma, ortam değişkenleri |
| `kurallar` | Kurulu desenler, adlandırma, kimlik kuralı ihlalleri |
| `yarim-is` | Bitmemiş akış, ölü kod, yutulan hata |

Her ajana verilecek görev metni:

```
ROL: <rol>
KOK: <proje kökü>
RAPOR: <kök>/_calisma/devralma/rapor.md

Bu rolün kapsamında projeyi oku ve ajan tanımındaki biçimde raporla.
Hiçbir dosyayı değiştirme.
```

Güvenlik ayrı bir iştir; mekanik tarama sır izlerini bulduysa `guvenlik-ajani`
de aynı anda çalıştırılır.

Dönen raporları `_calisma/devralma/ajan-<rol>.md` olarak yaz.

## 4. Öğrenilenleri birleştir

Beş raporu tek dosyada topla: `_calisma/devralma/ogrenilenler.md`

- Çakışan bulgu varsa **çakışmayı yaz**, birini seçip ötekini atma
- Her ajanın "CLAUDE.md'ye girmeli" maddelerini tek listede topla
- Soruları tek listede topla - bunlar kullanıcıya sorulacak

## 5. Planı göster ve onay al

```bash
python "$D" plan --yol "<kök>"
```

Kullanıcıya şunu göster:

1. Projenin ne olduğu - üç cümlelik özet
2. Kritik riskler - varsa en üstte
3. Ne üretilecek - dosya listesi
4. Neyin elle çözülmesi gerektiği
5. Ajanların çıkardığı sorular

**Burada dur ve onay iste.** Onay gelmeden altıncı adıma geçme.

## 6. Uygula

```bash
python "$D" uygula --yol "<kök>" --onay
```

Üretilenler:

| Dosya | İçerik |
|-------|--------|
| `CLAUDE.md` | Yığın, dizin düzeni, projeye özgü kurallar |
| `.claude/proje.json` | Proje tanımı (`tani.py` çıkarımıyla) |
| `hafiza/faz-plani.json` | Riskler ve yarım işlerden çıkan fazlar |
| `hafiza/durum.md` | Nerede kaldık kaydı |
| `hafiza/kararlar.md`, `hafiza/hatalar.md` | Boş defterler |
| `.gitignore` | Eksik yoksayma satırları eklenir |

Betik iskeleti üretir; **içeriği sen zenginleştirirsin.** Uygulamadan sonra
`CLAUDE.md`'yi aç ve ajanların "CLAUDE.md'ye girmeli" maddelerini
"Bu projede dikkat" başlığının altına işle. Üretilen taslakta boş bırakılan
yerler orada durmaz.

## 7. Kayda geç

```bash
P="${CLAUDE_PLUGIN_ROOT}/scripts/projeler"

python "$P/kayit.py" tara
python "$P/proje.py" dogrula
```

Tanımda eksik alan kaldıysa kullanıcıya sor, tahminle doldurma.

## 8. Kapanış

Şunu göster:

```
DEVRALINDI: <proje>
  Yığın      : <teknolojiler>
  Büyüklük   : <dosya> dosya / <satır> satır
  Üretilen   : <n> dosya
  Kritik risk: <n>
  Faz planı  : <n> faz

  Sırada: <ilk faz>
```

Kritik risk varsa kapanışta tekrar söyle. Sessizce geçme.

## İlgili

- `/proje-baslat` — sıfırdan proje
- `/kesif` — sorularla planlama
- `/guvenlik-tara` — derin güvenlik taraması
- `/faz` — üretilen faz planını yürütür
