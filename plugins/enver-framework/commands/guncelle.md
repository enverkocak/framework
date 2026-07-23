---
description: Framework'u tek komutla günceller - depodan son sürümü çeker, kurulumu yeniler
---

# Güncelle

Çerçeveyi en son sürüme getirir. Açılışta "GÜNCELLEME VAR" bildirimi
gördüğünde bu komutu çalıştır; tek adımda halleder.

## Ne yapar

1. Kaynak deponun yerini bulur (kurulumda kaydedilmiştir).
2. `git pull` ile son sürümü çeker.
3. Kurulumu yeniden çalıştırır - dosyaları `~/.claude` altında yeniler.
4. Sonunda `/reload-plugins` gerektiğini hatırlatır.

Yerel bir değişiklik varsa ya da ağ yoksa durur ve sebebini söyler;
hiçbir şeyi zorlamaz.

## Çalıştır

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/guncelleme.py" yap
```

Bittiğinde **sen** şunu çalıştır (bunu komut yapamaz, istemci yapar):

```
/reload-plugins
```

## Yalnız bakmak istersen

Güncellemeyi uygulamadan "var mı" diye bakmak için:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/guncelleme.py" kontrol
```

## Notlar

- Güncelleme **hiçbir zaman kendiliğinden** olmaz. Açılışta yalnız haber
  verilir; uygulamak senin kararın.
- Uzak depo günde bir kez yoklanır; her oturumda ağ trafiği olmaz.
- Güncelleme geçmişi ve neyin neden değiştiği: `DEGISIKLIKLER.md`.
