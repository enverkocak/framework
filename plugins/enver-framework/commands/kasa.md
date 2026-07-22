---
description: Parola korumali kasa - sifre ve anahtarlari acar, okur, gunceller, kilitler
---

# Kasa

Şifreler, sunucu bilgileri ve anahtarlar şifreli olarak `kasa/kasa.kilit` içinde durur.
Parola verilmeden okunamaz.

## Komutlar

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/kasa/kasa.py"

python "$K" durum              # kilitli mi açık mı, kalan süre
python "$K" ac                 # parola sorar, oturumu açar
python "$K" liste              # kasadaki dosyaları listeler
python "$K" oku <dosya>        # bir dosyanın içeriğini gösterir
python "$K" yaz <dosya>        # dosya ekler veya günceller (içerik stdin'den)
python "$K" kilitle            # oturumu kapatır
python "$K" parola             # parolayı değiştirir
```

## Kullanım akışı

1. Kullanıcı bir sunucu/şifre bilgisi isterse **önce `durum`** çalıştır.
2. Kilitliyse kullanıcıya sor: *"Kasa kilitli. Parolayı girmen gerekiyor."*
   Parolayı **sen üretme, sen tahmin etme, konuşmaya yazdırma.**
   Kullanıcının kendisinin çalıştırması için komutu ver:
   ```
   ! python <kasa yolu> ac
   ```
3. Açıldıktan sonra `liste` ve `oku` ile ihtiyacı karşıla.
4. İş bitince `kilitle` öner.

## Kesin kurallar

- Kasadan okunan değer **ekrana tam basılmaz** — sadece gereken yerde kullanılır.
- Kasa içeriği **log'a, commit'e, dosyaya yazılmaz.**
- Parola **konuşmaya yazılmaz**; kullanıcı kendi terminalinde girer.
- Kasa dosyasını doğrudan okumaya çalışma — koruma engeller, zaten şifrelidir.
- İş bitince kasayı kilitle.

## İlk kurulum

Düz metin bir klasörü kasaya çevirmek için:

```bash
python "$K" kur --kaynak vault
```

Kurulumdan sonra düz metin kaynağı **mutlaka arşivle**, projede bırakma:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ortak/arsiv.py" vault "Kasa duz metin kaynagi" "Kasa sifrelendi."
```

## İlgili

- `/guvenlik-tara` — sır sızıntısı taraması
- `/index` — bütün komutlar
