---
description: Sürümü tek komutla yükseltir - altı yeri birden günceller, DEGISIKLIKLER'e başlık açar
---

# Sürüm

Sürüm numarası altı yerde geçer (plugin, marketplace, ikisinin `.ornek`'i,
iki README). Bu araç hepsini aynı anda yükseltir; biri unutulmaz.

## Şu anki sürüm ve tutarlılık

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/surum.py" durum
```

## Yükselt

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/surum.py" yukselt kucuk   # 2.13.0 -> 2.13.1
python "${CLAUDE_PLUGIN_ROOT}/scripts/surum.py" yukselt orta    # 2.13.0 -> 2.14.0
python "${CLAUDE_PLUGIN_ROOT}/scripts/surum.py" yukselt buyuk   # 2.13.0 -> 3.0.0
```

| Tür | Ne zaman |
|-----|----------|
| `kucuk` | Hata düzeltme, küçük ekleme |
| `orta` | Yeni özellik, geriye uyumlu |
| `buyuk` | Kırıcı değişim, büyük yeniden yapı |

## Yükseltmeden sonra

Araç dosyaları hazırlar; **gerisi sana kalır:**

1. `DEGISIKLIKLER.md`'de açılan başlığı doldur — **ne** değişti ve **neden**.
2. Testi çalıştır: `tumunu-calistir.sh`.
3. commit + push.

## Kural

Her commit sürüm artırmaz. Sürüm **yayını** işaretler. Yalnız mevcut sürümü
belgeleyen değişiklikler (kılavuz düzeltmesi, README sayısı) sürüm artırmaz.
