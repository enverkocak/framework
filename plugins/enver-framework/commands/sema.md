---
description: Gorsel sistem semasi - hangi projede ne calisiyor, ne amacla, hangi projeye bagli
---

# Sistem Şeması

Bütün projeler ve aralarındaki bağlantılar tek sayfada, görsel olarak.
Kutular projeler, oklar aralarındaki veri akışı. Bir kutuya tıklayınca
o projenin ayrıntısı yanda açılır.

## Komutlar

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/projeler/sema.py"

python "$S" uret          # şemayı üret
python "$S" uret --ac     # üret ve tarayıcıda aç
python "$S" ozet          # metin özeti (tarayıcı gerekmez)
```

Çıktı `_calisma/sistem-semasi.html` dosyasına yazılır. Tek dosyadır,
dışarıdan hiçbir şey yüklemez, çevrimdışı açılır.

## Şemayı okuma

- **Soldan sağa akar.** Kimseden veri almayan projeler solda, onlardan
  beslenenler sağda.
- **Renkli şerit** projenin durumunu gösterir (canlıda, yarım, geliştirmede...).
- **Altta ayrı bölüm**, bağlantısı tanımlanmamış projeler içindir.
- **Kutuya tıkla** → görev, sunucu, veritabanı, içinde çalışan servisler.

## Bağlantı tanımlama

Şemadaki okların çıkması için projelerin birbirini tanıması gerekir.
Bir projenin tanımına:

```json
"baglantilar": [
  { "hedef": "diger-proje", "tur": "webhook", "aciklama": "Yeni kayıt bildirimi" }
]
```

`tur` alanı okun üstünde etiket olarak görünür: `webhook`, `api`, `veritabani`,
`dosya`, `bildirim` gibi.

## Servis tanımlama

Bir projenin içinde ne çalıştığı:

```json
"servisler": [
  { "ad": "web", "tur": "site", "gorev": "Müşteri arayüzü" },
  { "ad": "cron", "tur": "zamanlanmis", "gorev": "Gecelik fiyat güncelleme" }
]
```

## Ne zaman güncellenir

Şema her çalıştırmada yeniden üretilir; ayrı bir güncelleme gerekmez.
Yeni proje eklendiğinde önce `/projeler` altında `kayit.py tara` çalıştır.

## İlgili

- `/projeler` — metin olarak proje panosu
- `/ara` — her yerde arama
