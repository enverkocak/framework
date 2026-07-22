# Framework kuralları

> Bu dosya gerektiğinde okunur, her zaman yüklü değildir.
> Kısa özeti `CLAUDE.md` içinde durur.

---

## 1. Kimlik

Geliştirici bilgisi her zaman aynıdır ve tek yerden gelir:

Kimlik bilgisi **koda gömülmez**; kurulumda kaydedilir ve ayardan okunur:

```bash
python scripts/kurulum/sihirbaz.py kur --gelistirici "<ad>" --site "<site>" --eposta "<adres>"
```

Belgelerde `ayarlar.kimlik_satiri()` ile kullanılır.

Kodda, yorumlarda, commit mesajlarında ve dokümantasyonda **araç izi bırakılmaz**.
Ortak yazar (`Co-Authored-By`) satırı hiçbir commit'e eklenmez.

### İki kademeli iz kuralı

| Alan | Kural |
|------|-------|
| **Müşteri projeleri** | Sıfır iz. İstisnası yoktur. |
| **Framework'ün kendi deposu** | Muaf — kurulum talimatları, şema adresleri ve klasör adları teknik zorunluluktur. |

Muafiyet, depo kökündeki `.iz-muaf` işaret dosyasıyla tanımlanır.
`iz-kontrol.py` dosyadan yukarı doğru çıkarak bu işareti arar.

**`.iz-muaf` müşteri projelerine asla konulmaz.**

---

## 2. Güvenlik

- Kasa dosyaları (`vault/`) git'e eklenmez, log'a yazılmaz, çıktıda gösterilmez, kopyalanmaz.
- `.env`, kimlik bilgisi ve anahtar içeren dosyalar commit edilmez.
- Müşteri sunucusunda **sadece** belirtilen proje dizininde çalışılır.
  Diğer sitelere dokunulmaz — bu kural `sunucu-koruma.py` ile zorlanır.
- **Bütün depolar gizli (private).** Açmak gerekirse depo arayüzünden elle yapılır;
  komut satırından açma girişimi `git-gizlilik-koruma.py` tarafından engellenir.

---

## 3. Veri ve düzen

### Hiçbir veri silinmez
Silme yerine arşivleme yapılır. Arşiv motoru: `scripts/ortak/arsiv.py`

### Standart dizinler

| Dizin | Ne için | Git'e girer mi |
|-------|---------|----------------|
| `_calisma/` | Geçici işler, testler, denemeler | Hayır |
| `_arsiv/` | İşi biten her şey, notuyla | Hayır |
| `gunluk/` | Oturum kayıtları | Hayır |

### Ana dizin temiz kalır
Geçici ve test amaçlı hiçbir dosya ana dizinde bırakılmaz.
İşi biten `_arsiv/` altına, tarihli klasöre, `NEDEN.md` notuyla taşınır.

### Arşiv kaydının içeriği
Her arşiv klasöründe `NEDEN.md` bulunur:
ne yapıldı, neden yapıldı, ne zaman, sonuç ne oldu.
`_arsiv/INDEX.md` bütün kayıtları listeler ve aranabilir tutar.

---

## 4. Dil

Her şey Türkçe: arayüz, yorumlar, hata mesajları, dokümantasyon.

### Karakter kuralı

| Yer | Türkçe karakter |
|-----|-----------------|
| Komut adları, klasör adları, değişken/fonksiyon adları | **Kullanılmaz** (ASCII) |
| Yorum satırları, arayüz metinleri, web siteleri, hata mesajları | **Kullanılır**: ö ç ü ğ ı ş İ |

### Metin katmanı
Kullanıcıya görünen hiçbir metin koda gömülmez.
Hepsi `diller/<kod>.json` içinde durur, `scripts/ortak/metin.py` üzerinden okunur.
Yeni dil eklemek tek dosya çevirmekten ibarettir.

---

## 5. İzin ve onay

- Bir işlem engellendiğinde **neden engellendiği Türkçe açıklanır**.
- Yetki istenirken **ne için istendiği Türkçe yazılır**. Kullanıcı ne onayladığını bilmeden onay vermez.
- **Tam yetki modu** açıkken faz bitene kadar soru sorulmaz.
  İstisnalar (bu modda bile durdurur):
  - Kasa parolası
  - Silme girişimi
  - Başka müşteri dizinine erişim
  - Canlı ortama çıkış

---

## 6. Faz düzeni

Faz planı varsa sırasına uyulur. Faz atlanmaz.
Her fazın sonunda **kapı kontrolü** vardır; geçilmeden sonraki faza geçilmez.

Kapı kontrolü otomatik testtir — sonucu sayıyla raporlanır:
`N geçti, M kaldı`. M sıfır değilse kapı kapalıdır.

---

## 7. Bilgiye erişim

| İhtiyaç | Kaynak |
|---------|--------|
| Sunucu / kimlik bilgisi | `~/.claude/vault/index.md` (parola korumalı) |
| Proje bilgisi | Proje `CLAUDE.md` ve proje index'leri |
| Deploy bilgisi | `~/.claude/bilgi/deploy-rehberi.md` |
| Şablon | `~/.claude/sablonlar/index.md` |
| Komut rehberi | `/index` |
