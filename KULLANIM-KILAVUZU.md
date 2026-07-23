# Kullanım Kılavuzu

Enver Framework'ün günlük kullanımı. Ne zaman hangi komutu çalıştıracağını,
hangi kuralın neden var olduğunu anlatır.

**Geliştirici:** Enver KOCAK · enverkocak.com · mail@enverkocak.com

---

## İçindekiler

1. [Günlük akış](#günlük-akış)
2. [Yeni proje başlatma](#yeni-proje-başlatma)
3. [Komut rehberi](#komut-rehberi)
4. [Korumalar — ne engelleniyor, neden](#korumalar)
5. [Kasa](#kasa)
6. [Hafıza ve çoklu bilgisayar](#hafıza-ve-çoklu-bilgisayar)
7. [Faz motoru ve tam yetki](#faz-motoru-ve-tam-yetki)
8. [Tasarım](#tasarım)
9. [Teslim](#teslim)
10. [Güncelleme](#güncelleme)
11. [Sorun giderme](#sorun-giderme)

---

## Günlük akış

### Oturum açıldığında

Hiçbir şey yapmana gerek yok. Açılış kancası otomatik olarak şunu getirir:

- Hangi makinedesin
- Son çalışma başka makinede miydi (yerel bilgi eski olabilir)
- **Nerede kalmıştık** — son oturumun özeti
- Son kararlar ve son çözülen hatalar

Getirmezse: `python plugins/enver-framework/scripts/hafiza/oturum.py brifing`

### Çalışırken

Sistem arka planda kaydediyor: hangi komutu çalıştırdın, hangi dosyayı
değiştirdin. **Parolalar kayda geçmeden gizleniyor.**

Bir karar verdiğinde ya da bir hata çözdüğünde **hemen kaydet**:

```bash
H="plugins/enver-framework/scripts/hafiza"

python "$H/defter.py" karar ekle "<başlık>" "<gerekçe>"
python "$H/defter.py" hata ekle "<belirti>" "<çözüm>" --nerede "<bağlam>"
```

Bir hataya başlamadan **önce** ara — daha önce çözülmüş olabilir:

```bash
python "$H/defter.py" hata ara "<belirti>"
```

### Oturum biterken

```bash
python "$H/oturum.py" bitir --not "<devir notu>" --sirada "<sıradaki iş>"
python plugins/enver-framework/scripts/senkron/senkron.py gonder
```

---

## Yeni proje başlatma

**Doğrudan koda geçme.** Sıra şudur:

### 1. Keşif (dört aşama, atlanamaz)

```bash
K="plugins/enver-framework/scripts/plan/kesif.py"

python "$K" baslat --proje "<ad>" --musteri "<müşteri>"
python "$K" sorular                  # bu aşamada ne sorulacak
python "$K" yaz "<bulgu>"            # cevabı kaydet
python "$K" ilerle                   # sonraki aşama
```

| Aşama | Ne yapılır |
|-------|-----------|
| 1. İstek toplama | Müşteriye sor, cevapları **onun ağzından** yaz |
| 2. Araştırma | Ekstra neler olabilir, ne unutuluyor — araştır |
| 3. Netleştirme | Araştırmadan çıkanları sor, belirsizlik bırakma |
| 4. Plan | Fazlara böl, her faza kapı kontrolü koy |

Keşif bitmeden `durum` komutu **"KODLAMAYA GEÇİLMEZ"** der.

> **Küçük işler:** Tek dosyalık düzeltme için dört aşama gereksiz.
> Ölçüt: bir günden uzun sürecekse ya da müşteriye teslim edilecekse keşif yapılır.

### 2. Proje tanımı

```bash
P="plugins/enver-framework/scripts/projeler"

python "$P/proje.py" olustur --ad "<ad>" --gorev "<ne yapacak>" --musteri "<kim>"
python "$P/tani.py" bu               # boş alanları otomatik doldur
python "$P/proje.py" dogrula
```

Tanıma **parola yazılmaz.** Gizli bilgi kasada durur; tanımdaki
`kasa_anahtari` alanı yalnızca kasadaki kaydı işaret eder.

### 3. Tasarım brifingi

```bash
T="plugins/enver-framework/scripts/tasarim"

python "$T/ilham.py" site <örnek-adres>     # beğenilen siteyi çözümle
python "$T/kimlik.py" uret                   # özgün kimlik üret
python "$T/ilham.py" yazitipi sec --karakter <karakter>
python "$T/kimlik.py" css --hedef <proje>/stil/kimlik.css
python "$T/cihaz.py" css --hedef <proje>/stil/cihaz.css
```

### 4. Faz planı

```bash
F="plugins/enver-framework/scripts/faz"

python "$K" plana-dok                # keşiften faz planı üret
python "$F/faz.py" ekle <no> "<ad>" --kapi "<test komutu>"
```

---

## Komut rehberi

Bütün komutlar: `/index`

### Günlük

| Komut | Ne zaman |
|-------|----------|
| `/index` | Hangi komut var, nasıl kullanılır |
| `/panel` | Genel bakış |
| `/hafiza` | Nerede kaldık, karar ve hata defterleri |
| `/ara` | "Şunu nerede yazmıştık?" |
| `/durum-kaydet` | Oturumu kapatırken |

### Proje

| Komut | Ne zaman |
|-------|----------|
| `/kesif` | Yeni iş başlarken — kodlamadan önce |
| `/projeler` | Bütün projelerin durumu, projeye geçmeden sorgu |
| `/sema` | Görsel sistem şeması — hangi proje neye bağlı |
| `/proje-baslat` | Yeni proje iskeleti |
| `/faz` | Faz durumu, çalışma modu, tam yetki |

### Tasarım

| Komut | Ne zaman |
|-------|----------|
| `/tasarim` | Kimlik üretimi, ilham, kalıp denetimi, imza, cihaz katmanı |

### Güvenlik ve bakım

| Komut | Ne zaman |
|-------|----------|
| `/kasa` | Şifre ve anahtarlar |
| `/saglik` | Framework gerçekten çalışıyor mu |
| `/senkron` | Bilgisayar değiştirirken |
| `/guvenlik-tara` | Teslimden önce |
| `/guncelle` | Açılışta "GÜNCELLEME VAR" görünce |

### Sunucu ve operasyon

| Komut | Ne zaman |
|-------|----------|
| `/monitoring` | Sunucu sağlığı, SSL, disk |
| `/log-izle` | Hata arıyorken |
| `/db-yonetimi` | Veritabanı işleri |
| `/backup` | Yedekleme |
| `/git-islemleri` | Dal, commit, birleştirme |
| `/canli-kontrol`, `/web-kontrol` | Site çalışıyor mu |

---

## Korumalar

**On koruma** arka planda çalışır. Hiçbiri sessizce engellemez;
her engelleme **Türkçe gerekçeyle** gelir: ne yapılacaktı, neden engellendi,
nasıl düzeltilir.

| Koruma | Ne engeller |
|--------|-------------|
| `veri-koruma` | Silme komutları. Yıkıcı komutlarda onay ister |
| `kasa-koruma` | Kasaya doğrudan erişim, koda sır yazma |
| `sunucu-koruma` | Müşteri sunucusunda izinsiz dizine erişim |
| `git-gizlilik-koruma` | Depoyu herkese açık yapma girişimi |
| `iz-kontrol` | Kodda üretim aracı izi |
| `yazim-kontrol` | Kimlikte Türkçe karakter, metinde eksik Türkçe |
| `tam-yetki` | Tam yetki modunda rutin işlere izin verir |
| `kalite-kapisi` | Tam yetkide "bitti" demeyi kapıya bağlar |
| `oturum-kayit` | Ne yapıldığını sessizce kaydeder |
| `oturum-acilis` | Açılışta brifing verir |

### Neden silme engelleniyor

**Hiçbir veri silinmez.** Silme yerine arşivleme yapılır:

```bash
python plugins/enver-framework/scripts/ortak/arsiv.py <yol> "<iş adı>" "<neden>"
```

Arşiv `_arsiv/` altında tarihli klasörde durur, yanında `NEDEN.md` bulunur.
Altı ay sonra "bu neydi" sorusunun cevabı orada.

### Neden ana dizine geçici dosya yazılamıyor

Ana dizin temiz kalır. Geçici işler `_calisma/` altında yapılır,
biten iş arşivlenir.

---

## Kasa

Şifreler `kasa/kasa.kilit` içinde **şifreli** durur.

```bash
K="plugins/enver-framework/scripts/kasa/kasa.py"

python "$K" durum          # kilitli mi açık mı
python "$K" ac             # parola sorar, 60 dakika açık kalır
python "$K" liste          # kasadaki dosyalar
python "$K" oku <dosya>    # içeriği göster
python "$K" yaz <dosya>    # ekle ya da güncelle
python "$K" kilitle        # kapat
```

**Önemli:**
- Parolayı **kendi terminalinde** gir; konuşmaya yazma
- Çözülmüş içerik **hiçbir zaman diske yazılmaz**
- Süre dolunca kasa kendiliğinden kilitlenir
- Kasa dosyasını doğrudan okumaya çalışma — koruma engeller, zaten şifreli

---

## Hafıza ve çoklu bilgisayar

### İki ayrı alan

| Alan | Ne | Senkron olur mu |
|------|-----|-----------------|
| `hafiza/` | Özetlenmiş kalıcı bilgi | **Evet** |
| `gunluk/` | Ham oturum kaydı | Hayır — makinede kalır |

### Yeni bilgisayara geçtiğinde

```bash
S="plugins/enver-framework/scripts/senkron"

python "$S/makine.py" durum              # bu makine tanınıyor mu
python "$S/makine.py" tanit --ad "<ad>"  # tanımıyorsa kaydet
python "$S/senkron.py" cek               # güncel hafızayı al
```

Çekme işlemi bittiğinde otomatik brifing gelir: nerede kalmıştın.

### İş bitiminde

```bash
python "plugins/enver-framework/scripts/hafiza/oturum.py" bitir --not "..."
python "$S/senkron.py" gonder
```

### Çakışma

`gonder`, depoda bizde olmayan kayıt varsa **durur ve üzerine yazmaz**.
`cek`, yerelde işlenmemiş değişiklik varsa durur.

Bu iki kural birlikte, iki makinede yapılan işin birbirini silmesini engeller.

---

## Faz motoru ve tam yetki

### Faz

```bash
F="plugins/enver-framework/scripts/faz"

python "$F/faz.py" durum      # aktif faz ve ilerleme
python "$F/faz.py" plan       # bütün fazlar
python "$F/faz.py" kapi       # kapı kontrolünü çalıştır
python "$F/faz.py" ilerle     # kapı geçtiyse sonraki faza geç
```

**"Bitti" bir görüş değil, ölçüm sonucudur.** Kapı kontrolü bir komuttur;
raporundaki "kaldı" sayısı sıfırsa kapı açılır.

### Çalışma modları

```bash
python "$F/mod.py"            # durum
python "$F/mod.py" tam-yetki  # aç
python "$F/mod.py" dikkatli   # varsayılana dön
```

```bash
python "$F/mod.py" durum      # açık mı, hangi mod?
```

| Mod | Ne yapar |
|-----|----------|
| `dikkatli` | Varsayılan. Riskli işlemlerde onay ister |
| `hizli` | Rutin işlerde soru azalır |
| `sunucuda` | En temkinli |
| `tam-yetki` | **Hiç soru sormaz** — izin kutusu çıkmaz |

### Tam yetki — ne yapar, neyi yapamaz

Açıkken o **"Do you want to proceed? 1 Yes / 2 Yes all / 3 No"** kutusu
**hiç çıkmaz.** `git push`, `deploy`, `DROP` dahil her şey sessizce geçer.
İş baştan sona kesintisiz akar.

**Ama sert engeller delinmez.** Bunlar ayrı korumalarda tanımlı ve tam
yetki bunları geçemez — "engelle" her zaman "izin ver"i yener:

| Tam yetki açıkken bile durur | Nerede |
|------------------------------|--------|
| Dosya silme (`rm`, `Remove-Item`) | veri-koruma (E7) |
| Kasaya doğrudan erişim | kasa-koruma (E1) |
| Depoyu herkese açık yapma | git-gizlilik-koruma |
| Harita dışı sunucu dizini | sunucu-koruma |

> **Bilinçli seçim:** Tam yetki modunda "her yes'in ne için olduğunu gör"
> kuralı (E16) kapanır. Yalnız bu modda; `dikkatli`'ye dönünce geri gelir.
>
> **Dikkat:** `DROP TABLE` veri siler ama "onay" katmanındaydı, dosya
> silme gibi "kesin engel" değil — o yüzden tam yetkide sorulmadan çalışır.
> Dosya silme (`rm`) ise her zaman engellenir.

---

## Tasarım

**Kural: iki proje aynı görünmez.**

### Kimlik

```bash
T="plugins/enver-framework/scripts/tasarim"

python "$T/kimlik.py" uret       # bu projeye görsel kimlik
python "$T/kimlik.py" liste      # kullanılmış bütün kimlikler
python "$T/kimlik.py" css --hedef <proje>/stil/kimlik.css
```

Üretilen kimlik, kullanılmış ana tonlardan **en az 28 derece** uzak durur.
Bütün renk çiftleri okunabilirlik ölçütünden geçer (4.5:1).

### Cihaz katmanı

Beş sınıf: **mobil · büyük mobil · tablet · web · masaüstü**

```bash
python "$T/cihaz.py" liste                 # sınıflar ve eşikler
python "$T/cihaz.py" css --hedef cihaz.css
python "$T/cihaz.py" iskelet               # çalışan sayfa iskeleti
python "$T/cihaz.py" denetle <yol>
```

Ekran genişliği tek ölçüt değil: dokunmatik mı, hareket azaltma isteniyor mu,
ekran yoğunluğu ne — hepsine bakılır.

### Teslimden önce denetim

```bash
python "$T/kalip-denetim.py" tara <proje>   # şablon işaretleri
python "$T/cihaz.py" denetle <proje>        # cihaz uyumu
python "$T/imza.py" denetle                 # imza ön planda mı
```

---

## Teslim

```bash
I="plugins/enver-framework/scripts/is"
S="plugins/enver-framework/scripts/sunucu"

python "$S/kontrol.py" tara <proje>    # güvenlik, erişilebilirlik, arama, başarım
python "$I/teslim.py" kontrol          # teslime hazır mı
python "$I/teslim.py" hazirla          # paketi üret
```

Üretilen belgeler:

| Belge | İçerik |
|-------|--------|
| Kullanım kılavuzu | Müşteri ne yapacağını bilsin |
| Teknik belge | Başka biri devralabilsin |
| Erişim bilgileri | **Parola YOK** — bilginin nerede olduğu |
| Teslim tutanağı | İmzalanacak belge, kapsam dışı dahil |
| Kişisel veri listesi | Sekiz maddelik kontrol |

### Deploy

```bash
python "$S/deploy.py" kontrol
```

Zorunlu sıra: **hazırlık → denetim → yedek → test → onay**

Betik **asıl gönderimi kendisi yapmaz.** Canlıya çıkış açık bir insan kararıdır.

---

## Güncelleme

Açılışta yeni sürüm varsa brifingin **en üstünde** görürsün:

```
GÜNCELLEME VAR: 2.13.0 → 2.14.0
  Ne değişti:
    - ...
  Güncellemek için tek komut:  /guncelle
```

Uzak depo **günde bir kez** yoklanır — her oturumda ağa çıkılmaz. Ağ
yoksa hiçbir şey gösterilmez, açılış aksamaz.

### Güncellemek

```
/guncelle
```

`git pull` yapar, kurulumu yeniler. Bittiğinde **sen** şunu çalıştır:

```
/reload-plugins
```

Terminalden aynısı:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/guncelleme.py" yap
```

### Neden otomatik değil

Sessiz güncelleme çalışırken davranışı değiştirir ve yerel işinle
çakışabilir. Bu yüzden çerçeve **yalnız haber verir** — uygulamak senin
kararın. Sadece "var mı?" diye bakmak için:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/guncelleme.py" kontrol
```

> Bildirim 2.13.0'dan itibaren çalışır. Daha eski bir kurulumu ilk kez
> elle güncellemen gerekir; ondan sonra kendisi haber verir.

---

## Sorun giderme

### "Bir şey çalışmıyor gibi"

```bash
python plugins/enver-framework/scripts/saglik/saglik.py bak
```

Yedi alanı ölçer. **Korumaların yalnız kayıtlı değil, gerçekten çalıştığı**
ölçülür — her korumaya gerçek girdi verilir.

### Komple test

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

12 faz kapısı, 105 senaryo, sağlık kontrolü, işlevsel ve güvenlik doğrulamaları.
Yaklaşık 35 saniye.

### Bir koruma yanlış engelliyor

Engelleme mesajı **neden** engellendiğini ve **nasıl düzeltileceğini** yazar.
Gerçekten yanlışsa ilgili koruma dosyasındaki desen düzeltilir; sonra:

```bash
python plugins/enver-framework/scripts/saglik/saglik.py kancalar
```

### Komut çalışmadan önce ne olacağını görmek

```bash
python plugins/enver-framework/scripts/kuru-deneme.py "<komut>"
```

Komutu çalıştırmadan, **gerçek korumalara sorarak** ne olacağını gösterir.

### Yedekten geri dönmek

```bash
python plugins/enver-framework/scripts/sunucu/yedek.py liste
python plugins/enver-framework/scripts/sunucu/yedek.py geri <yedek> --onayla
```

Geri dönmeden önce mevcut hâl otomatik yedeklenir; **geri dönüş de geri alınabilir.**

---

## Kalıcı kurallar

- Kodda ve commit'te üretim aracı izi yok. Geliştirici: **Enver KOCAK**
- Türkçe: arayüz, yorum, hata mesajı. Kimliklerde ASCII, metinlerde tam Türkçe
- **Hiçbir veri silinmez** — arşivlenir, notlanır
- Ana dizin temiz kalır: geçici işler `_calisma/`, biten işler `_arsiv/`
- Her izin isteği **Türkçe gerekçeli**
- **Bütün depolar gizli.** Açmak gerekirse arayüzden elle
