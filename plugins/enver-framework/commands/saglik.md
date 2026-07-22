---
description: Framework saglik kontrolu - korumalar gercekten calisiyor mu, cakisma var mi, paylasima hazir mi
---

# Sağlık

Bu komutun varlık sebebi somut bir olaydır: korumalar aylarca yazılıydı ama
ayar dosyasına kaydedilmedikleri için **hiçbiri çalışmıyordu.** Kimse fark
etmedi, çünkü kimse bakmadı.

**"Kayıtlı" ile "çalışıyor" farklı şeylerdir.** Bu kontrol ikisini de ölçer:
her korumaya gerçek bir girdi verilir, beklenen kararı verip vermediğine bakılır.

## Komutlar

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/saglik/saglik.py"

python "$S" bak            # bütün kontroller
python "$S" kancalar       # yalnız korumalar
python "$S" cakisma        # iki şey aynı işi mi yapıyor
python "$S" istatistik     # ne var, ne kullanılıyor
```

## Neye bakılır

| Kontrol | Ne ölçer |
|---------|----------|
| Korumalar | Kayıtlı mı **ve** gerçekten tepki veriyor mu |
| Betikler | Sözdizimi geçerli mi |
| Hafıza | Yazılıyor mu, doğru yerde mi (senkron olan girer, ham günlük girmez) |
| Kasa | Kurulu mu, biçimi doğru mu, depoya sızıyor mu |
| Çakışma | Aynı adlı komut, harf farkıyla çakışan dosya, aynı açıklama |
| Dil | Dil dosyaları aynı anahtarları taşıyor mu |
| Düzen | Ana dizinde beklenmeyen şey var mı |

## Kurulum ve paylaşım

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/kurulum/sihirbaz.py"

python "$K" kontrol              # ortam hazır mı
python "$K" kur                  # kurulumu yap
python "$K" bilgi                # kayıtlı kimlik
python "$K" paylasima-hazirla    # kişisel veri içermeyen kopya üret
```

### Paylaşırken dikkat

`hafiza/` klasörü **kendi kullanımında depoya girer** — çoklu bilgisayar
senkronu buna dayanır. Ama içinde müşteri adları, sunucu dizinleri, cihaz
adresleri ve kararlar vardır.

Depoyu biriyle paylaşacaksan **önce temiz kopya üret:**

```bash
python "$K" paylasima-hazirla
```

Bu komut kasayı, hafızayı ve proje kayıtlarını çıkarır; kalan dosyalarda
kişisel iletişim bilgisi kalmış mı diye tarar.

## Ne zaman çalıştırılır

- **Yeni bilgisayara kurulumdan sonra** — korumalar gerçekten devrede mi
- **Framework güncellendikten sonra** — bir şey bozuldu mu
- **Paylaşmadan önce** — kişisel veri sızıyor mu
- **Kuşku duyulduğunda** — "acaba çalışıyor mu?" sorusunun cevabı

## İlgili

- `/index` — bütün komutlar
- `/faz` — faz motoru ve kapı kontrolleri
