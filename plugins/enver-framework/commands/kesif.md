---
description: Kodlamadan onceki dort asama - istek toplama, arastirma, netlestirme, plan
---

# Keşif

**Kodlamaya doğrudan geçilmez.** Önce dört aşama işletilir:

| Aşama | Amaç |
|-------|------|
| 1. İstek toplama | Ne isteniyor? Müşterinin ağzından, olduğu gibi |
| 2. Araştırma | Ekstra neler olabilir? Ne unutuluyor? |
| 3. Netleştirme | Belirsizlikler kapatılır, sorular sorulur |
| 4. Plan | Fazlara bölünür, kapı kontrolleri konur |

Aşama atlanamaz. En pahalı hata, yarım anlaşılmış bir işe başlayıp
sonra baştan yazmaktır.

## Komutlar

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/plan/kesif.py"

python "$K" baslat --proje "<ad>" --musteri "<müşteri>"
python "$K" durum          # hangi aşamadayız
python "$K" sorular        # bu aşamada ne sorulacak
python "$K" yaz "<bulgu>"  # cevabı kaydet
python "$K" ilerle         # sonraki aşamaya geç
python "$K" ozet           # keşfin tamamı
python "$K" plana-dok      # faz planı üret
```

## Kullanım

1. `baslat` ile keşfi aç
2. `sorular` ile o aşamada ne sorulacağını gör
3. Kullanıcıya sor, cevapları `yaz` ile kaydet
4. `ilerle` ile sonraki aşamaya geç
5. Dördüncü aşama bitince `plana-dok` ile faz planını üret

## Kodlamaya ne zaman geçilir

```bash
python "$K" durum
```

**"KODLAMAYA GEÇİLMEZ"** yazıyorsa geçilmez. Kullanıcı ısrar ederse
eksik olanı söyle, riski açıkça belirt.

## Küçük işler

Tek dosyalık düzeltme için dört aşama gereksizdir.
Ölçüt: **bir günden uzun sürecekse ya da müşteriye teslim edilecekse** keşif yapılır.

Emin değilsen sor: *"Keşif yapalım mı, doğrudan mı geçelim?"*

## İlgili

- `/faz` — faz motoru
- `/tasarim` — tasarım brifingi (keşiften sonra)
- `/projeler` — proje tanımı
