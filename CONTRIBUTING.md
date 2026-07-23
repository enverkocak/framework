# Katkı / Contributing

Türkçe aşağıda · English below.

---

## Türkçe

Katkın için teşekkürler. Bu çerçeve gerçek işlerde kullanılıyor; küçük ve net
katkılar en kolay değerlendirilir.

### Hata bildirme

1. Önce [açık konulara](../../issues) bak — aynısı var mı?
2. Yoksa **Hata bildirimi** şablonuyla yeni konu aç.
3. Şunları yaz: ne yaptın, ne bekledin, ne oldu, işletim sistemin ve sürüm
   (`/surum` ya da `plugin.json`).

### Öneri

**Özellik önerisi** şablonuyla aç. "Ne" değil, **"hangi sorunu çözüyor"** ile
başla — çözülecek gerçek bir ihtiyaç en ikna edici gerekçedir.

### Kod göndermeden önce

Testleri çalıştır, hepsi geçmeli:

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

### Kurallar (bu depoya özel)

- **Türkçe:** arayüz, yorum, hata mesajı Türkçe. Değişken/dosya adlarında ASCII,
  metinlerde tam Türkçe karakter (ç, ş, ğ, ü, ö, ı).
- **Üretim aracı izi yok:** kodda, yorumda, commit'te yapay zekâ/araç referansı
  bulunmaz.
- **Veri silinmez:** silme yerine arşivlenir.
- **Sürüm + not:** işlevsel değişiklik `surum.py` ile yükseltilir ve
  `DEGISIKLIKLER.md`'ye *ne + neden* yazılır.

Bu kurallar kancalarla zorlanır; testler bunları denetler.

---

## English

Thanks for contributing. This framework is used in real work; small, clear
changes are the easiest to accept.

### Reporting a bug

1. Check [open issues](../../issues) first.
2. If it's new, open an issue with the **Bug report** template.
3. Include: what you did, what you expected, what happened, your OS, and the
   version (`/surum` or `plugin.json`).

### Suggesting a feature

Open one with the **Feature request** template. Start with the **problem it
solves**, not the feature itself.

### Before sending code

Run the tests; all must pass:

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

### Rules (specific to this repo)

- **Turkish-first:** UI, comments and error messages are Turkish. ASCII in
  identifiers/filenames; full Turkish characters in prose.
- **No tool traces:** no AI/tool references in code, comments or commits.
- **Data is never deleted:** archive instead of delete.
- **Version + notes:** functional changes bump the version via `surum.py` and add
  a *what + why* entry to `DEGISIKLIKLER.md`.

These rules are enforced by hooks and checked by the test suite.
