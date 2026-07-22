---
description: Tek arama noktasi - hafiza, bilgi notlari, proje tanimlari ve icindekiler belgelerinde birlikte arar
---

# Ara

Bilgi birden çok yerde birikiyor. "Şunu nerede yazmıştık" sorusu için
dört ayrı yere bakmak gerekmesin diye hepsi tek aramadan geçer.

## Komut

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ara.py" "<sorgu>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/ara.py" "<sorgu>" --sinir 10 --baglam 2
```

## Nereler aranır

| Alan | İçerik |
|------|--------|
| hafıza | durum, kararlar, çözülen hatalar, oturum özetleri |
| proje tanımı | bütün projelerin görevi, sunucusu, teknolojisi |
| bilgi notu | statik notlar, deploy rehberi, teknoloji notları |
| içindekiler | klasörlerin ne barındırdığı |
| komut, kural | framework belgeleri |

## Kasa aranmaz

Kasa içeriği şifrelidir, arama ona bakmaz. Sorgu gizli bilgiyle ilgiliyse
arama bunu söyler ve kasayı açmayı önerir.

## Türkçe karakter

Arama ö/o, ç/c, ş/s farkına takılmaz. `sifre` yazsan da `şifre` bulunur.

## Ne zaman kullanılır

- **Bir hataya başlamadan önce** — daha önce çözülmüş olabilir.
- **"Bunu neden böyle yapmıştık"** — karar defterinde yazıyordur.
- **"Şu projede hangi veritabanı vardı"** — proje tanımında.
- **Bir konuya dair her şeyi görmek** — dört alanı birden tarar.

## İlgili

- `/hafiza` — kayıtların kendisi
- `/projeler` — proje panosu
- `/kasa` — gizli bilgiler
