# Global Kurallar

> Bu bir **örnek** dosyadır. Kendi kurallarınla değiştir ve `CLAUDE.md`
> olarak kaydet. Buradaki değerler yer tutucudur.

## KİMLİK KURALLARI

1. **Kod yorum satırlarında** üretim aracı adı geçmez. Yorum, kodu
   yazanın sesidir. Belge, düz metin, dize değeri, komut ve yol serbesttir.
2. Geliştirici bilgisi her zaman aynı olacak:
   `<ADIN> | <siten> | <e-postan> | <telefonun>`
3. Ortak yazar (`Co-Authored-By`) satırı hiçbir commit'e eklenmez.

## GÜVENLİK KURALLARI

4. Kasa dosyaları **asla**: depoya eklenmez, log'a yazılmaz, çıktıda
   gösterilmez, kopyalanmaz.
5. `.env`, kimlik bilgisi ve anahtar içeren dosyalar commit edilmez.
6. Müşteri sunucusunda **yalnız** belirtilen proje dizininde çalışılır.
   Diğer sitelere dokunulmaz.

   Sunucu ve dizin bilgisi şurada tanımlanır:
   `~/.claude/plugins/enver-framework/references/sunucu-haritasi.json`

## ÇALIŞMA KURALLARI

7. Arayüz, yorumlar, değişkenler, fonksiyonlar ve hata mesajları
   **tek dilde** olacak. (Varsayılan: Türkçe)
8. Türkçe özel karakterler (ç, ş, ğ, ü, ö, ı) **yalnız kullanıcıya görünen
   metinlerde**. Değişken ve dosya adlarında ASCII kullanılır.
9. Faz planı varsa faz sırasına uy. Fazı atlamadan, kapı kontrolünü
   geçmeden ilerleme.

## VERİ KURALLARI

10. **Hiçbir veri silinmez.** Silme yerine arşivlenir, notu yazılır.
11. Ana dizin temiz kalır. Geçici işler `_calisma/`, biten işler `_arsiv/`.

## BİLGİ ERİŞİMİ

| İhtiyaç | Kaynak |
|---------|--------|
| Sunucu / kimlik bilgisi | Kasa (parola korumalı) |
| Proje bilgisi | Proje tanımı ve index'ler |
| Komut rehberi | `/index` |
| Kurallar | `~/.claude/plugins/enver-framework/references/kurallar.md` |

## KOMUTLAR

| Komut | Ne yapar |
|-------|----------|
| `/index` | Bütün komutlar ve kullanımları |
| `/kesif` | Kodlamadan önceki dört aşama |
| `/faz` | Faz durumu, çalışma modu, tam yetki |
| `/hafiza` | Nerede kaldık, kararlar, hatalar |
| `/kasa` | Şifreler ve anahtarlar |
| `/saglik` | Framework gerçekten çalışıyor mu |
| `/guncelle` | Yeni sürüme tek komutla geç |

---

## English

**Your own working rules.** This file ships as an example; replace the
placeholders with your details. Whatever you write here applies to every
session in this project.

The identity rules keep your name on your work. The security rules keep
secrets out of the repository. The working rules define the language,
the phase order and what "done" means.

Rules written here are read at the start of every session; the ones that
must never be forgotten are additionally enforced by protection hooks.
