# Değişiklikler

Enver Framework'ün sürüm geçmişi.

Kayıt tutma biçimi: her sürümde **ne değişti** ve **neden** yazılır.
"Ne" olmadan geçmiş anlamsız, "neden" olmadan öğretici değildir.

---

## 3.1.0 — Var olan projeler devralınabiliyor

Çerçeve bugüne kadar sıfırdan başlayan projeye göre kurulmuştu:
`/proje-baslat` şablon açıyor, `/kesif` sorularla ilerliyordu. Oysa işlerin
çoğu **zaten var olan** bir koda giriliyor - eski bir müşteri sitesi,
uzun süre dokunulmamış bir depo. Böyle bir projede çerçevenin bütün
yetenekleri (faz motoru, hafıza, kapılar) boşta duruyordu; kimse yirmi
bin satırlık bir projenin `CLAUDE.md`'sini elle yazmıyor.

`/proje-devral` bu boşluğu kapatır: projeyi okur, öğrendiğini yazıya
döker, **onay alır**, sonra çerçeveye bağlar.

- **`/proje-devral` komutu** — sekiz adım: mekanik tarama, beş paralel
  ajanla derin okuma, birleştirme, plan, onay, uygulama, kayıt, kapanış.
- **`devral.py` tarama motoru** — dizin haritası ve rolleri, giriş
  noktaları, bağımlılıklar, depo geçmişi ve en çok dokunulan dosyalar,
  yarım iş izleri, depoya girmiş sır, kimlik kuralına aykırı satırlar,
  eksik çerçeve dosyaları.
- **`devralma-ajani`** — beş rol (mimari, veri, süreç, kurallar,
  yarım iş) paralel çalışır; hiçbiri dosya değiştirmez.
- **`proje-devral` becerisi** — çerçeve dosyası olmayan bir dizinde iş
  istenirse kendiliğinden devreye girer.

**Neden onaysız yazılmıyor:** devralınan proje çoğu zaman müşteriye ait
ve çalışır durumdadır. Tarama aşaması hiçbir dosyaya dokunmaz, yalnız
`_calisma/devralma/` altına rapor bırakır; `uygula --onay` denmeden tek
dosya yazılmaz ve var olan bir dosyanın üzerine hiçbir koşulda yazılmaz.

**Neden sır değerleri raporlanmıyor:** tarama koda gömülü parola ve
anahtar arıyor. Bulduğunu rapora yazsa rapor kendisi bir sızıntı olurdu.
Yalnız `dosya:satır` ve izin türü bildirilir.

**Kurulum kılavuzu düzeltildi** — eklentiyi etkinleştirme adımı eski
pazar yeri adını (`enver-local`) ve yanlış yolu gösteriyordu. Ayrıca
kapsam (`user` / `project` / `local`) bölümü eklendi: eklentinin bütün
projelerde mi yoksa tek depoda mı çalışacağı artık yazıyor.

## 3.0.0 — Gerçek Claude Code eklentisi: tek komutla kurulum

Çerçeve artık standart bir Claude Code eklentisi. Herkes tek satırla
ekleyip kurabiliyor; korumalar da eklentiyle birlikte geliyor.

```
/plugin marketplace add enverkocak/framework
/plugin install enver-framework@enver-framework
```

**Neden kırıcı sürüm (3.0.0):** kurulum yöntemi değişti. Eskiden korumalar
`kurulum.sh` ile `settings.json`'a kaydediliyordu; artık eklentinin
`hooks.json`'u getiriyor. Var olan bir kurulumdan geçen kişinin kurulumu
yeniden yapması gerekir.

- **Kancalar eklentinin içine taşındı** — `plugins/enver-framework/hooks/`
  + `hooks.json`. Yollar `${CLAUDE_PLUGIN_ROOT}` ile veriliyor, makineden
  bağımsız. **Neden:** Claude Code eklentisi bileşenlerini (komut, beceri,
  ajan, kanca) kendi kökünde bekler; kancalar repo kökündeyken eklenti
  tam değildi.
- **Kök `.claude-plugin/marketplace.json`** — `/plugin marketplace add
  enverkocak/framework` bunu okuyor. Eklenti kendi `.claude-plugin/plugin.json`
  manifestini taşıyor.
- **Tek teslim.** `kurulum.sh` artık kanca KAYDETMEZ; korumalar eklentinin
  `hooks.json`'undan gelir. Böylece çift kayıt (çift çalışma) olmaz.
  Kurulum yalnız kimlik, kasa/hafıza klasörleri ve güncelleme kaydını yapar.
- **`claude plugin validate` temiz** — plugin ve marketplace manifestleri
  doğrulamadan geçiyor. Yol boyunca üç gerçek sorun çıktı ve düzeltildi:
  iki `SKILL.md`'de YAML hatası (açıklama içindeki `:` eşleme sanılıyordu),
  ve `commands/`+`agents/` içindeki üretilen `ICINDEKILER.md` dosyaları sahte
  komut/ajan oluşturuyordu (index üreteci artık bileşen dizinlerine yazmıyor).

### Ders (canlı göç tehlikesi)

Çalışan oturumun `settings.json`'unun işaret ettiği kancaları taşımak,
kırık PreToolUse kancaları `Bash` aracını bloke ettiği için oturumu
kilitledi. Kurtarma `PowerShell` ile oldu (`Bash` matcher'ına takılmıyor).
Bu tür göçler oturum sınırında yapılmalı, orta yerinde değil.

## 2.15.1 — CI düzeltmeleri (satır sonu + makineye özgü test)

İlk CI koşuları kırmızıydı. İki ayrı sebep:

- **Satır sonları.** Windows runner `.sh` dosyalarını `autocrlf=true` ile
  CRLF olarak checkout ediyordu; Git Bash `\r` yüzünden bütün testi
  düşürüyordu. `.gitattributes` ile tüm metin dosyaları LF'e sabitlendi.
- **Makineye özgü test.** `faz0`'ın "arşiv ve yedek" bölümü Enver'in
  makinesindeki sabit `D:/Projeler/_arsiv/...` yollarını doğruluyordu.
  Yerelde geçiyordu (o klasörler burada var), CI'da ve başka makinede
  kalıyordu. Artık o klasör yoksa kontrol atlanıyor — yokluğu bir eksiklik
  değil, "bu makineye özgü tarihsel kayıt".

Ders (yine): sabit makine yolu taşıyan bir test yalnız o makinede geçer.
"Kurulmamışlık bozukluk değildir" ilkesinin test tarafındaki karşılığı.

## 2.15.0 — Dünyaya açılış: İngilizce belge, CI, katkı altyapısı

Herkese açık depo yayında ama dışarıdan bakınca eksikti: keşfedilir değildi,
yalnız Türkçeydi, "canlı proje" görünmüyordu. Bu sürüm onu gerçek bir açık
kaynak projesine dönüştürür.

- **İngilizce README (`README.en.md`)** + iki README'nin başında
  "Türkçe | English" geçişi. **Neden:** sadece Türkçe = sadece Türkiye;
  dünyanın büyük kısmı ve arama motorları dışarıda kalıyordu. E18 dil
  niyetinin doğal devamı.
- **Rozetler ve akış diyagramı** — lisans, sürüm, CI rozetleri; "nasıl
  çalışır" artık mermaid diyagramı (GitHub yerel olarak çiziyor, resim
  gerektirmez).
- **Sürekli tümleştirme (CI)** — `.github/workflows/test.yml`: her push ve
  PR'da bütün test takımı Windows runner'da çalışır. Yeşil "passing" rozeti
  bir bakışta güven verir. **Neden Windows:** testler orada kanıtlandı.
- **Katkı altyapısı** — `CONTRIBUTING.md`, `SECURITY.md`, issue şablonları
  (hata/öneri, iki dilli), PR şablonu. İnsanların nasıl katkı ve bildirim
  yapacağı belli.
- **Sürüm aracı sağlamlaştırıldı** — README'lerde sürüm artık ilk satırda
  değil (orada dil geçişi var), rozette. `surum.py` ve `faz0` sürümü ilk
  satırda değil, dosyanın herhangi bir yerinde arıyor. Kendi üzerinde
  denenince çıkan bir hataydı, düzeltildi (dogfooding).

### Neden mermaid, İngilizce, CI hep birlikte

Keşfedilebilirlik tek bir şeye bağlı değil: arama motorları İngilizce
içeriği indeksler, GitHub konu etiketlerini sıralar, geliştiriciler yeşil
CI rozetine ve net bir README'ye güvenir. Hepsi birden olmadan "çok kişiye
ulaş" gerçekleşmiyor.

## 2.14.0 — Tek komutla sürüm yükseltme

Sürüm numarası altı dosyada geçiyordu: `plugin.json`, `marketplace.json`,
ikisinin `.ornek` kopyası ve iki README. Elle değiştirince biri unutuluyor,
`faz0` testi tutarsızlığı yakalayıp kapıyı kapatıyordu — ama önce hatayı
yapmak gerekiyordu.

- **`surum.py yukselt kucuk|orta|buyuk`** — altı yeri aynı anda yükseltir,
  hiçbiri unutulmaz. **Neden:** "her yayında sürüm + not" disiplinini elle
  sürdürmek altı ayrı düzenleme demekti; bir yeri atlamak kolaydı.
- **DEGISIKLIKLER'e taslak başlık** — yükseltme, tarihli boş bir sürüm
  başlığı açar; "ne + neden"i sen doldurursun. Not zorunlu kalır.
- **Tutarlılık kontrolü** — `surum.py durum` altı yerin aynı sürümde
  olduğunu doğrular. Yayın öncesi güvenlik ağı.
- **`/surum`** komutu eklendi.

### Not (sürümleme kuralı)

Her commit sürüm artırmaz. Sürüm **yayını** işaretler: yeni özellik → orta,
düzeltme → küçük, kırıcı değişim → büyük. Yalnız mevcut sürümü belgeleyen
değişiklikler (kılavuz, README sayısı) sürüm artırmaz.

## 2.13.0 — Tam yetki susar, güncelleme haber verir

İki gerçek istek: tam yetki modu soru sormaya devam ediyordu; kullananlar
yeni sürümden haberdar olmuyordu.

- **Tam yetki artık hiç soru sormaz.** Açıkken "Do you want to proceed?"
  kutusu çıkmaz; `git push`, `deploy`, `DROP` dahil her şey sessizce
  geçer. **Neden değişti:** eski hâlde geniş bir istisna listesi vardı ve
  bunlar bilerek soruyordu; günlük işte sürekli çıkınca "açtım ama hâlâ
  soruyor" oluyordu. Ayrıca `veri-koruma`'nın "onay iste"si, tam yetkinin
  "izin ver"ini eziyordu (en kısıtlayıcı kazanır), o yüzden onu da kesmek
  gerekti.
- **Sert engeller delinmedi.** Dosya silme (E7), kasa (E1), herkese açık
  depo ve harita dışı sunucu ayrı kancalarda durur; tam yetki bunları
  geçemez. Karar Enver'in: E16 ("her yes'in ne için olduğunu göreyim")
  yalnız tam yetki modunda kapanır, dikkatli modda geçerli kalır.
- **`mod.py durum`** çalışır hale geldi — modun açık mı olduğunu görmenin
  yolu yoktu; "açtım sanıyorum ama emin değilim" bundandı.
- **Açılışta "GÜNCELLEME VAR" bildirimi.** Uzak depo günde bir kez
  yoklanır; yeni sürüm varsa açılış brifinginin en üstünde sürüm farkı ve
  ne değiştiği görünür. **Neden bildirim, otomatik değil:** sessiz
  güncelleme çalışırken davranışı değiştirir ve yerel işle çakışabilir;
  Claude Code'un kendisi de yalnız haber verir.
- **`/guncelle` — tek komutluk güncelleme.** `git pull` + kurulumu kendisi
  yürütür, sonunda `/reload-plugins` hatırlatır. Kurulum artık klon
  konumunu kaydeder ki kurulu kopya kaynağın nerede olduğunu bilsin.

## 2.12.0 — Cihaza göre tasarım

**Faz 11.** Enver'in isteği (E20): her projede mobil, tablet, web ve
masaüstü için ayrı tasarım.

- **Beş cihaz sınıfı** — mobil, büyük mobil, tablet, web, masaüstü.
  Her birinin kendi yerleşimi, dokunma hedefi ve okuma genişliği var.
- **Cihazın kendisi de tanınıyor** — dokunmatik mı ince imleç mi, yatay mı
  dikey mi, hareket azaltma isteniyor mu, ekran yoğunluğu ne.
- **Cihaz uyumu denetimi** — görüntü alanı etiketi, ölçek kilidi, sabit
  genişlik, kesme noktası, dokunma hedefi, üzerine gelmeye bağımlı içerik.
- **Sayfa iskeleti** — üretilen iskelet kendi denetiminden geçiyor.

### Neden

Tek bir düzeni küçültüp büyütmek yeterli değil. 1024px'lik bir dokunmatik
ekran, aynı genişlikteki bir dizüstünden farklı davranmalı.

### Düzeltmeler

Faz numaraları metin olarak saklanıyordu; sıralama alfabetik oluyor ve
`0, 1, 10, 11, 2, 3...` sırası çıkıyordu. Bu, aktif fazın yanlış
hesaplanmasına yol açabilirdi. Numaralar sayıya çevrildi, eski kayıtları
onaran bir düzeltme eklendi, teste koruma kondu.

Faz 5 testi sabit "11 faz" bekliyordu; yeni faz eklenince bozuldu.
Sayı yerine yapı doğrulanıyor artık.

---

## 2.11.0 — Sağlık ve paylaşım

**Faz 10 tamamlandı. 11 fazın tamamı bitti.**

- **Sağlık kontrolü** — korumaların yalnız kayıtlı değil, gerçekten
  **çalıştığı** ölçülüyor. Her korumaya gerçek girdi verilip beklenen kararı
  verip vermediğine bakılıyor.
- **Çakışma denetimi** — aynı adlı komut, harf farkıyla çakışan dosya,
  aynı açıklamayı taşıyan komutlar yakalanıyor.
- **Kurulum sihirbazı** — ortam kontrolü, kimlik kaydı, koruma kaydı.
- **Paylaşıma hazırlama** — kişisel veri içermeyen temiz kopya üretiyor.
- **Dil dosyası tutarlılığı** — diller aynı anahtarları taşıyor mu denetleniyor.

### Neden

Korumalar aylarca yazılıydı ama ayar dosyasına kaydedilmedikleri için
**hiçbiri çalışmıyordu.** Kimse fark etmedi çünkü kimse bakmadı.
Sağlık kontrolü bu durumun tekrar etmemesi için var.

Paylaşım tarafında ince bir ayrım çıktı: `hafiza/` kendi kullanımda depoya
girmeli (çoklu bilgisayar senkronu buna dayanıyor), ama içinde müşteri adları
ve cihaz adresleri var. Paylaşılan kopyada bulunmamalı.

---

## 2.10.0 — Sektör ve veri araçları

- **Keşif motoru** — kodlamadan önce dört aşama: istek toplama, araştırma,
  netleştirme, plan. Aşama atlanamaz; keşif bitmeden "kodlamaya geçilmez" der.
- **Cihaz envanteri** — kamera, kayıt cihazı, ağ donanımı kayıtları.
  Envantere parola yazılamıyor; kod düzeyinde engelli.
- **Toplu dosya işlemleri** — adlandırma ve türe göre ayırma.
  Her işlem önce deneme olarak çalışıyor.

### Neden

Yarım anlaşılmış bir işe başlayıp sonra baştan yazmak en pahalı hatadır.
Envanter dosyası paylaşılabilir olmalı; parola içeren bir dosya paylaşılamaz.
Yüz dosyayı yanlış adlandırmak, doğru adlandırmaktan kolaydır.

---

## 2.9.0 — İş ve müşteri katmanı

- **Görev takibi** — her görevin kaynağı yazılıyor: müşteri isteği,
  kendi kararımız, bulunan hata, bakım işi.
- **Hizmet takvimi** — hosting, alan adı, sertifika, bakım tarihleri.
  Sertifika taramasının sonuçları takvime besleniyor.
- **Müşteri teslim paketi** — kılavuz, teknik belge, erişim bilgileri,
  teslim tutanağı, kişisel veri kontrol listesi.

### Neden

Erişim belgesine parola yazılmıyor; belge bilginin **nerede** durduğunu
söylüyor. Teslim belgeleri e-postayla dolaşır, parola dolaşmamalı.

---

## 2.8.0 — Operasyon ve sunucu

- **Yedek ve geri dönüş** — geri dönüşün kendisi de geri alınabiliyor.
- **Sertifika takibi** — 30 gün dikkat, 14 gün acil.
- **Deploy güvenlik zinciri** — hazırlık, denetim, yedek, test, onay.
  Bir adım kalırsa zincir durur.
- **Teslim öncesi denetimler** — güvenlik, erişilebilirlik, arama, başarım.

### Neden

Deploy betiği **asıl gönderimi kendisi yapmıyor.** Canlıya çıkış açık bir
insan kararı olmalı; otomatik gönderim zincirin bütün güvencesini tek bir
hatalı çalıştırmayla boşa çıkarabilir.

Kapı testleri üstel olarak tekrarlıyordu (her faz kendinden öncekileri,
onlar da kendi öncekilerini). Süre 2 dakikadan 22 saniyeye düştü.

---

## 2.7.0 — Tasarım özgünlüğü

- **Tasarım kimliği üreteci** — her projeye renk, tipografi, boşluk, köşe,
  derinlik ve karakter. Kullanılmış tonlardan en az 28 derece uzak durur.
- **Yazı tipi kataloğu** — 20 eşleşme, 10 karakter. Ağ yoksa yedek yığın.
- **Örnek site çözümlemesi** — yön tarifi çıkarır, kopyalama reçetesi değil.
- **Kalıp denetimi** — 15 kural. Şablon sayfada 13 bulgu, özgün sayfada sıfır.
- **İz kimliği** — beş biçim, her projeye en az kullanılmış olanı.
  Şirket bilgisi projeye göre değişebiliyor.

### Neden

Projelere bakanlar "bu otomatik üretilmiş" diyordu çünkü tasarımlar hep aynıydı.
Kopya hem etik değil hem de zaten aynılaşmaya götürüyor.

---

## 2.6.0 — Faz motoru ve tam yetki

- **Faz motoru** — plan, ilerleme, kapı kontrolü. "Bitti" bir görüş değil,
  ölçüm sonucu.
- **Tam yetki modu** — faz bitene kadar soru sorulmuyor.
- **Çalışma modları** — dikkatli, hızlı, sunucuda, tam yetki.
- **Kalite kapısı** — tam yetkide "bitti" demeyi kapıya bağlıyor.
- **İzole deneme alanı** — riskli değişiklik ayrı kopyada.

### Neden

Tam yetki **hız demek, kontrolsüzlük değil.** İstisna listesindeki işlemlerde
kanca karar vermiyor, sessiz kalıyor; kararı ilgili koruma veriyor.
Reddetme izin vermeye üstün olduğu için tam yetki hiçbir korumayı aşamıyor.

---

## 2.5.0 — Projeler beyni ve sistem şeması

- **Proje tanımı** — her proje kendini anlatıyor.
- **Çift kayıt** — asıl kayıt projede, yansıması framework hafızasında.
- **Merkezi pano** — bütün projeler durum sırasına göre.
- **Geçmeden sorgu** — başka projeye geçmeden bilgi alınabiliyor.
- **Görsel sistem şeması** — tek dosyalık HTML, dış kaynak yok.
- **Otomatik tanıma** — 23 projenin teknolojisi ve durumu çıkarıldı.
- **Tek arama** — hafıza, proje tanımları, notlar ve içindekiler birlikte.

---

## 2.4.0 — Hafıza ve süreklilik

- **Alan ayrımı** — `hafiza/` senkron olur, `gunluk/` makinede kalır.
- **Çoklu bilgisayar** — makine kimliği, çekme/gönderme, çakışma koruması.
- **Oturum hafızası** — parolalar kayda geçmeden gizleniyor.
- **Defterler** — karar defteri ve hata kütüphanesi.
- **Proje içi içindekiler** — açıklamalar dosyaların kendisinden okunuyor.
- **Durum satırı** — proje, makine, faz, kasa, maliyet.

### Neden

Üretilen belgenin adı önce `INDEX.md` idi. Windows dosya sistemi büyük/küçük
harf ayırmadığı için `bilgi/index.md`, `sablonlar/index.md` ve
`commands/index.md` üzerine yazıldı ve içerikleri kayboldu. Depodan geri alındı,
ad `ICINDEKILER.md` yapıldı, üretece çakışma kontrolü eklendi.

---

## 2.3.0 — Koruma kalkanı

- **Şifre kasası** — scrypt + Fernet. Çözülmüş içerik diske yazılmıyor.
- **Veri koruması** — silme engelleniyor, yıkıcı komutlarda onay isteniyor.
- **Kasa ve sır koruması** — koda sır yazılması engelleniyor.
- **Türkçe yazım denetimi** — kimliklerde ASCII, metinlerde tam Türkçe.
- **Sunucu haritası** — koruma sabit kod yerine haritadan okuyor.
- **Türkçe gerekçe standardı** — her engelleme aynı biçimde konuşuyor.
- **Sanal deneme** — komut çalışmadan gerçek korumalara soruluyor.

---

## 2.2.0 — Çekirdek iskelet

- **Dil katmanı** — kullanıcı metinleri koddan ayrıldı.
- **Betik katmanı** — deterministik işler kod oldu.
- **Arşivleme motoru** — tarihli klasör, neden notu, otomatik dizin.
- **Komut rehberi** — liste elle tutulmuyor, dizinler taranarak üretiliyor.
- **Windows desteği** — kurulum ve güncelleme betikleri.

### Neden

Eski kurulum betiği korumaları kopyalıyor ama **kaydetmiyordu.**
"Hiçbir koruma çalışmıyor" durumunun sebebi buydu.

---

## 2.1.0 — Acil temizlik

- Kasa depo geçmişinden çıkarıldı.
- Korumalar ayar dosyasına kaydedildi (daha önce hiç çalışmıyorlardı).
- Depo gizlilik kuralı eklendi.
- Duplikat komut arşivlendi.
- Sürümler tek noktada birleştirildi.

### Neden

Kasa dosyaları depo geçmişinde duruyordu. Depo gizli olduğu için dışarı
sızmadı, ancak geçmiş tamamen sıfırlandı ve tek temiz commit ile başlandı.
