---
description: Framework'u tek komutla günceller - depodan son sürümü çeker, kurulumu yeniler
---

# Güncelle

Çerçeveyi en son sürüme getirir. Açılışta "GÜNCELLEME VAR" bildirimi
gördüğünde bu komutu çalıştır; tek adımda halleder.

## Ne yapar

Önce **hangi yoldan kurulduğuna** bakar, çünkü çalışan kopya iki ayrı
yerde olabilir:

**Pazar yerinden kurulduysa** (`claude plugin install ...`) çalışan kopya
`~/.claude/plugins/cache/<eklenti>/<sürüm>/` altındadır. Bu durumda:

1. `claude plugin marketplace update` ile pazar yeri tazelenir.
2. `claude plugin update` ile eklenti son sürüme çekilir.
3. Depo klonuna **dokunulmaz**.

**Depo klonundan kurulduysa** eski yol işler: `git pull` + kurulumu
yeniden çalıştırma.

Ayrım şart: pazar yerinden kurulu bir makinede klon kurulumunu da
çalıştırmak `~/.claude/plugins/` altına ikinci, paralel bir kurulum
bırakır ve hangisinin canlı olduğu belirsizleşir.

Sonunda `/reload-plugins` gerektiğini hatırlatır. Yerel bir değişiklik
varsa ya da ağ yoksa durur ve sebebini söyler; hiçbir şeyi zorlamaz.

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
- Kurulu kopya çalışan koddan geride kalırsa açılışta ayrıca söylenir
  ("PAZAR YERI KOPYASI GERIDE"). Depo güncellenip eklenti eski sürümde
  kalabiliyor; bu fark eskiden hiç görünmüyordu.
- Uzak depo günde bir kez yoklanır; her oturumda ağ trafiği olmaz.
- Güncelleme geçmişi ve neyin neden değiştiği: `DEGISIKLIKLER.md`.

---

## English

**Update the framework** — invoke with `/guncelle` (or `/enver-framework:guncelle` if the short name does not resolve).

It first detects **how the framework was installed**. If it came from a
marketplace, the running copy lives in `~/.claude/plugins/cache/` and only
`claude plugin marketplace update` + `claude plugin update` refresh it —
the repository clone is left alone. If it was installed from a clone, the
old path applies: `git pull` + re-run the installer. Mixing the two would
leave a second, parallel installation behind.

Existing settings are preserved. When the installed copy falls behind the
running code, the session banner says so.
