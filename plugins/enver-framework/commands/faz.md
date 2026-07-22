---
description: Faz motoru - aktif faz, ilerleme, kapi kontrolu, calisma modu ve tam yetki
---

# Faz

Faz planı varsa sırasına uyulur, faz atlanmaz. Her fazın sonunda bir kapı
kontrolü vardır; geçilmeden sonraki faza geçilmez.

**"Bitti" bir görüş değil, ölçüm sonucudur.** Kapı kontrolü bir komuttur;
çıkış kodu ve rapordaki "kaldı" sayısı sıfırsa kapı açılır.

## Komutlar

```bash
F="${CLAUDE_PLUGIN_ROOT}/scripts/faz"

python "$F/faz.py" durum      # aktif faz ve ilerleme
python "$F/faz.py" plan       # bütün fazlar
python "$F/faz.py" kapi       # kapı kontrolünü çalıştır
python "$F/faz.py" ilerle     # kapı geçtiyse sonraki faza geç

python "$F/mod.py"            # çalışma modu durumu
python "$F/mod.py" tam-yetki  # tam yetki modunu aç
python "$F/mod.py" dikkatli   # varsayılana dön

python "$F/izole.py" ac <ad>      # izole deneme alanı aç
python "$F/izole.py" kapat <ad>   # kapat (arşivlenir)
```

## Çalışma modları

| Mod | Ne yapar |
|-----|----------|
| `dikkatli` | Varsayılan. Riskli işlemlerde onay ister |
| `hizli` | Rutin işlerde soru azalır, riskliler yine sorulur |
| `sunucuda` | En temkinli. Müşteri sunucusunda kullanılır |
| `tam-yetki` | Faz bitene kadar soru sorulmaz |

## Tam yetki modu

Açıldığında faz bitene kadar izin sorulmaz, iş kesintisiz akar.
Faz bittiğinde durulur ve tek seferde rapor verilir.

**Tam yetki hız demektir, kontrolsüzlük değil.** Bu modda bile duran işlemler:

- Kasa parolası istenmesi
- Silme girişimi
- Uzak sunucuya erişim
- Canlıya çıkış ve yayınlama
- Depo görünürlüğü ayarı
- Geri alınamaz veritabanı işlemleri
- Ödeme işlemleri

Bu istisnalarda tam yetki kancası **karar vermez**, sessiz kalır; kararı
ilgili koruma verir. Reddetme her zaman izin vermeye üstündür.

### Açmadan önce

Tam yetki açılacaksa **aktif fazın kapı kontrolü tanımlı olmalı.**
Tanımlı değilse nerede duracağı belli olmaz; mod bunu uyarır.

### Kalite kapısı

Tam yetki açıkken iş bitirilmek istendiğinde kapı otomatik çalışır.
Geçmediyse çalışma sürdürülür — eksik iş "bitti" diye kapanmaz.

## İzole deneme alanı

Riskli bir fikri denemek için asıl projeyi bozmadan ayrı kopya açar.
Beğenmezsen kapatırsın, asıl projede iz kalmaz.
Kapatırken içerik silinmez, arşivlenir.

## Kullanım akışı

1. `faz.py durum` — nerede olduğumuzu gör
2. İşi yap
3. `faz.py kapi` — ölç
4. Kapı açıksa `faz.py ilerle`, değilse eksikleri gider

## İlgili

- `/hafiza` — nerede kaldık
- `/index` — bütün komutlar
