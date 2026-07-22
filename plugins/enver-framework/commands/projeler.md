---
description: Butun projeler tek ekranda - durum, musteri, gorev; projeler arasi gecis ve gecmeden sorgu
---

# Projeler

Bütün projelerin durumu tek yerden görünür: hangisi yarım, hangisi canlıda,
hangisi bekliyor. Bir projeye geçmeden de bilgi alınabilir.

## Komutlar

```bash
P="${CLAUDE_PLUGIN_ROOT}/scripts/projeler"

python "$P/kayit.py" liste                    # bütün projeler
python "$P/kayit.py" liste --durum yarim      # yalnız yarım kalanlar
python "$P/kayit.py" goster <proje>           # bir projenin ayrıntısı
python "$P/kayit.py" sor <proje> "<soru>"     # geçmeden bilgi al
python "$P/kayit.py" tara                     # yeni proje var mı bak
python "$P/kayit.py" yansit                   # tanımları merkezi hafızaya kopyala

python "$P/proje.py" goster                   # bu projenin tanımı
python "$P/proje.py" dogrula                  # tanım eksiksiz mi
python "$P/tani.py" bu                        # boş alanları otomatik doldur
```

## Kullanım

**"Hangi projeler yarım kaldı?"** → `kayit.py liste --durum yarim`

**"X projesinin veritabanı neydi?"** → `kayit.py sor X "veritabani"`
Bu, projeye geçmeden cevap verir; sen bulunduğun projede kalırsın.

**"X projesine geç"** → önce `kayit.py goster X` ile yolunu al,
sonra kullanıcıya o dizinde yeni oturum açmasını öner. Çalışma dizinini
kendiliğinden değiştirme.

**Yeni proje eklendiğinde** → `kayit.py tara`, sonra `tani.py hepsi`.

## Proje tanımı

Her proje kendini `<proje>/.claude/proje.json` içinde anlatır:
ne işe yaradığı, hangi sunucuda, hangi veritabanıyla, neye bağlı olduğu.

Tanım iki yerde tutulur:

| Yer | Ne için |
|-----|---------|
| Projenin kendi klasörü | Asıl kayıt — projeyle birlikte taşınır |
| `hafiza/projeler/` | Yansıma — proje taşınsa ya da disk bağlı olmasa bile bilgi kalır |

Asıl kayıt her zaman üstündür.

## Kesin kural

Tanıma **parola, anahtar ya da erişim bilgisi yazılmaz.** Gizli bilgi kasada
durur; tanımdaki `kasa_anahtari` alanı yalnızca kasadaki kaydı işaret eder.

## Otomatik tanıma

`tani.py` klasöre bakıp doldurabildiğini doldurur: teknolojiler, açıklama,
son çalışma tarihine göre durum tahmini. Doldurduğu alanlar tanımda
**tahmin** diye işaretlenir — doğrulanması gerekir.

Elle yazılmış alanların üzerine asla yazmaz.

## İlgili

- `/sema` — görsel sistem şeması
- `/ara` — her yerde arama
- `/kasa` — gizli bilgiler
