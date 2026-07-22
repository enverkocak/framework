# Kurulum Kılavuzu

Bu framework'ü sıfırdan kurmak için. Hiçbir adım varsayılmaz.

---

## Bu nedir

Proje yönetim altyapısıdır. Şunları yapar:

- **Korur** — silmeyi engeller, sırların koda yazılmasını durdurur,
  müşteri sunucusunda yanlış dizine dokunmayı bloklar
- **Hatırlar** — nerede kaldığını, hangi kararı neden verdiğini,
  hangi hatayı nasıl çözdüğünü tutar
- **Takip eder** — projeler, görevler, hizmet tarihleri, cihaz envanteri
- **Özgünleştirir** — her projeye farklı görsel kimlik üretir, şablon
  görünümünü denetler
- **Ölçer** — "bitti" demeyi kapı kontrolüne bağlar

Tek kullanıcı içindir; ekip aracı değildir.

---

## Gereksinimler

| Gereksinim | Neden | Zorunlu mu |
|-----------|-------|-----------|
| Python 3.9+ | Bütün betikler Python | **Evet** |
| Git | Senkron ve yedek | Evet (bunlar olmadan çalışmaz) |
| `cryptography` paketi | Şifre kasası | Kasa kullanılacaksa |
| Bash | Kapı testleri | Test çalıştırılacaksa |

Windows'ta Git kurulumu Bash'i de getirir.

### Kontrol

```bash
python --version
git --version
python -c "import cryptography; print('kurulu')"
```

Şifreleme paketi yoksa:

```bash
python -m pip install cryptography
```

---

## Kurulum

### 1. Dosyaları al

```bash
git clone https://github.com/enverkocak/framework
cd framework
```

### 2. Ortamı kontrol et

```bash
python plugins/enver-framework/scripts/kurulum/sihirbaz.py kontrol
```

Eksik varsa söyler. Eksik olan özellik çalışmaz ama kurulum yine yapılabilir.

### 3. Kur

**Windows:**
```powershell
.\kurulum.ps1
```

**Linux / Mac:**
```bash
chmod +x kurulum.sh
./kurulum.sh
```

Bu betik:
- Dosyaları kullanıcı klasörüne kopyalar
- **Korumaları ayar dosyasına kaydeder** — bu adım atlanırsa hiçbir koruma çalışmaz

### 4. Kimliğini gir

Framework başka biri için yazıldı; kendi bilgilerini girmen gerekir:

```bash
python plugins/enver-framework/scripts/kurulum/sihirbaz.py kur \
  --gelistirici "<adın>" \
  --site "<siten>" \
  --eposta "<e-postan>" \
  --sirket "<şirketin>"
```

### 5. Eklentiyi etkinleştir

```
/plugin marketplace add ~/.claude/plugins
/plugin install enver-framework@enver-local
/reload-plugins
```

### 6. Kurulumu doğrula

```bash
python plugins/enver-framework/scripts/saglik/saglik.py bak
```

**"Framework sağlıklı"** görmelisin. Görmüyorsan aşağıya bak.

---

## İlk adımlar

### Komutları gör

```
/index
```

27 komut, ne işe yaradıkları ve nasıl kullanıldıkları.

### Bu makineyi tanıt

Birden çok bilgisayar kullanacaksan:

```bash
python plugins/enver-framework/scripts/senkron/makine.py tanit --ad "<bu bilgisayarın adı>"
```

### Kasayı kur

Şifrelerin şifreli dursun:

```bash
python plugins/enver-framework/scripts/kasa/kasa.py kur --kaynak <şifre-klasörün>
```

Parola sorar — **kendi terminalinde** gir, en az 8 karakter.

Sonra düz metin kaynağı arşivle:

```bash
python plugins/enver-framework/scripts/ortak/arsiv.py <şifre-klasörün> \
  "Kasa duz metin kaynagi" "Kasa sifrelendi."
```

### Projelerini tara

```bash
P="plugins/enver-framework/scripts/projeler"

python "$P/kayit.py" kok --ekle "<projelerinin bulunduğu klasör>"
python "$P/kayit.py" tara
python "$P/tani.py" hepsi      # teknoloji ve durum tahmini
python "$P/kayit.py" liste
```

### Görsel şemayı üret

```bash
python "$P/sema.py" uret --ac
```

---

## Klasör düzeni

```
framework/
├── hooks/                  Korumalar
├── plugins/enver-framework/
│   ├── commands/           Eğik çizgi komutları
│   ├── skills/             Beceriler
│   ├── agents/             Alt ajanlar
│   ├── scripts/            Betik katmanı
│   ├── references/         Kurallar, haritalar, kataloglar
│   └── diller/             Arayüz metinleri (tr, en)
├── bilgi/                  Statik notlar
├── sablonlar/              Proje şablonları
│
├── hafiza/                 Kalıcı hafıza — depoya girer, senkron olur
├── gunluk/                 Ham oturum kaydı — makineye özel
├── kasa/                   Şifreli kasa — depoya girmez
├── _calisma/               Geçici işler — depoya girmez
└── _arsiv/                 İşi biten her şey, notuyla — depoya girmez
```

**Ana dizin temiz kalır.** Geçici dosya oraya yazılamaz; koruma engeller.

---

## Dil

Varsayılan Türkçe. Değiştirmek için:

```bash
python -c "
import sys; sys.path.insert(0, 'plugins/enver-framework/scripts/ortak')
import ayarlar; ayarlar.yaz({'dil': 'en'})
"
```

Mevcut diller `plugins/enver-framework/diller/` altında.
Yeni dil eklemek: `tr.json` dosyasını kopyalayıp çevir.
Dosyalar aynı anahtarları taşımalı — sağlık kontrolü bunu denetler.

---

## Kurulumdan sonra

### Neyin devrede olduğunu gör

```bash
python plugins/enver-framework/scripts/saglik/saglik.py bak
python plugins/enver-framework/scripts/saglik/saglik.py istatistik
```

### Komple test

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

12 faz kapısı, 105 senaryo, sağlık ve güvenlik doğrulamaları.
Yaklaşık 35 saniye. Hepsi geçmeli.

---

## Sorun giderme

### "Korumalar çalışmıyor"

En sık sebep: kurulum betiği korumaları kopyaladı ama **kaydetmedi.**

```bash
python plugins/enver-framework/scripts/kurulum/kanca-kaydet.py \
  hooks .claude/settings.json
```

Sonra doğrula:

```bash
python plugins/enver-framework/scripts/saglik/saglik.py kancalar
```

> Bu framework'ün geçmişinde tam olarak bu olay yaşandı: korumalar aylarca
> yazılıydı ama kaydedilmedikleri için hiçbiri çalışmıyordu. Sağlık kontrolü
> bunun tekrar etmemesi için var.

### "Kasa çalışmıyor"

```bash
python -m pip install cryptography
```

### "Türkçe karakterler bozuk görünüyor"

Betikler UTF-8 yazar; sorun konsol kodlamasındadır. Windows'ta:

```powershell
chcp 65001
```

Dosyaların içeriği doğrudur; yalnız ekran görünümü etkilenir.

### "Komut bulunamıyor"

```
/reload-plugins
```

Sonra `/index` ile listeyi gör.

### "Test yavaş çalışıyor"

Faz testleri normalde kendinden öncekileri de çalıştırır. Tek bir fazı
denerken tekrarı kapat:

```bash
ENVER_GERILEME_ATLA=1 bash plugins/enver-framework/scripts/testler/faz5-kapi.sh
```

---

## Bilinmesi gerekenler

### Hiçbir veri silinmez

Silme komutları engellenir. Silmek yerine arşivlenir:

```bash
python plugins/enver-framework/scripts/ortak/arsiv.py <yol> "<iş>" "<neden>"
```

Bu bir tercih değil, kuraldır. Alışkanlık değiştirmek gerekebilir.

### Depolar gizli olur

Depoyu herkese açık yapma girişimi engellenir. Gerçekten açılacaksa
depo arayüzünden elle yapılır.

### Kişisel veri paylaşılmaz

`hafiza/` klasörü kendi kullanımda depoya girer (çoklu bilgisayar senkronu
buna dayanır) ama içinde müşteri adları ve proje bilgileri vardır.

Depoyu biriyle paylaşacaksan **önce temiz kopya üret:**

```bash
python plugins/enver-framework/scripts/kurulum/sihirbaz.py paylasima-hazirla
```

### Her engelleme gerekçeli gelir

Bir işlem engellendiğinde şunlar yazılır: ne yapılacaktı, neden engellendi,
nasıl düzeltilir. Sessiz engelleme yoktur.

---

## Kaldırma

Framework kullanıcı klasörüne kopyalanır. Kaldırmak için:

1. `~/.claude/settings.json` içinden koruma kayıtlarını çıkar
2. `~/.claude/plugins/enver-framework/` klasörünü kaldır
3. `~/.claude/enver/` altındaki ayarları kaldır

Proje klasörlerindeki `hafiza/`, `kasa/` ve `_arsiv/` **kendi verindir**;
kaldırma bunlara dokunmaz.

---

## Lisans ve kaynak

Bu framework tek bir geliştiricinin çalışma biçimi etrafında kuruldu.
Kendi ihtiyacına göre değiştirmen beklenir — kurallar, korumalar ve
kontroller senin işine göre ayarlanabilir.

Değiştirmesi en muhtemel yerler:

| Dosya | Ne için |
|-------|---------|
| `plugins/enver-framework/references/sunucu-haritasi.json` | Kendi sunucuların ve projelerin |
| `plugins/enver-framework/references/dizin-duzeni.json` | Ana dizinde ne bulunabilir |
| `hooks/veri-koruma.py` | Hangi komutlar engellensin |
| `plugins/enver-framework/diller/tr.json` | Arayüz metinleri |
| `plugins/enver-framework/references/yazi-tipi-eslesmeleri.json` | Tasarım kataloğu |
