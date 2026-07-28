# Değişiklikler

English: [`DEGISIKLIKLER.en.md`](DEGISIKLIKLER.en.md)

Enver Framework'ün sürüm geçmişi.

Kayıt tutma biçimi: her sürümde **ne değişti** ve **neden** yazılır.
"Ne" olmadan geçmiş anlamsız, "neden" olmadan öğretici değildir.

---

## 3.3.4 — Kurulum artik kasaya hic dokunmuyor

"Guncelleme yapinca kasa kirilir mi" diye soruldu. Olculdu: kirilmiyordu.
Ama sebebi bir koruma degil, bir tesadufu: kaynakta `vault/` klasoru yok,
o yuzden kopyalama adimi bos geciyordu. **Klasor bir gun geri gelse
kullanicinin sifreli kasasi `-Force` ile ezilirdi** ve bunu olcen hicbir
sey yoktu.

Kural zaten aciktir: kasa dosyalari git'e girmez, log'a yazilmaz, ekrana
basilmaz ve **kopyalanmaz**. Kurulum bu kuralin disinda tutulmustu.

**Ne degisti:** Iki kurulum betigi de kasayi kopyalamayi tumden birakti.
Klasorun varligi saglanir, icine dokunulmaz. Kaynakta bir kasa klasoru
varsa tasinmaz, "KOPYALANMADI (kural geregi)" diye haber verilir. Kasa
`kasa.py kur` ile olusur ve makineye ozeldir.

**Olcum:** `kurulum-testleri.py` 24'ten **32 senaryoya** cikti. En kotu
durum kurulur: kaynakta da kasa var, hedefte de, hem de **ayni adli
dosya** - kopyalayan bir kurulum burada gercekten ezer. Kurulu kasanin
**bayt bayt** ayni kaldigi olculur.

Senaryolarin gercekten yakaladigi ayrica denendi: kopyalama satiri
bilerek geri konuldu, iki isletim sisteminde de yedi kontrol dustu.
Satir farkli bicimde yazildiginda da dustu - metinde belirli bir satir
aranmiyor, "kopyalayan hicbir satir kasadan soz etmiyor" olculuyor.

**Belge:** Iki kurulum kilavuzunda da kasanin nerede yasadigi ve neyin
onu goturdugu yazili: `git pull` guvenli (kasa izlenmiyor), ama depoyu
yeni bir klasore yeniden klonlamak kasayi geride birakir, `git clean
-xfd` siler. Kasa senkron olmaz.

### Ayni kosuda cikan ikinci bulgu: uretilen kopya proje sanildi

Tam takim iki yerde birden kirmizi yandi ve ikisinin de koku ayniydi:
paylasim icin uretilen ayna klasoru **bagimsiz bir proje** sayiliyordu.

- Kayitta "tanimsiz proje" olarak goruluyor, Faz 4 kapisi dusuyordu.
- Daha kotusu: klasor adinin parcalari kisisel veri deseni oluyordu.
  `...-framework-acik` kayitliyken **`framework`** aranan kelime haline
  geldi, 96 dosyada eslesti ve temiz kopya **paylasilamaz** ilan edildi.
  Yani yayin hatti, hicbir gercek sizinti yokken kilitlenmisti.

Iki duzeltme: (1) `paylasima-hazirla` hedefe `.enver-ayna` isareti
birakir, tarama bu isareti tasiyan klasoru proje saymaz - kayit
silinmez, yalniz listede gosterilmez. Isaretin icine yol ya da kimlik
yazilmaz, cunku o dosya paylasilan klasorde durur. (2) `framework`,
`cerceve`, `kaynak`, `surum`, `yedek` yaygin kelime listesine girdi:
genel bir teknik kelime kisisel veri sayilmaz.

Faz 10'a uc kontrol eklendi. Biri karsi olcum yapiyor: isaretsiz ayni
klasor proje **sayilmali** - yoksa kontrol "hicbir sey proje degil"
diyerek bos yere gecerdi.

**Tam takim: 622 gecti, 0 kaldi.**

## 3.3.3 — Guncelleme yolu Mac ve Linux'ta hic yurumuyordu

"Ilk surumu kuran biri sona nasil gecer" sorusu soruldu. Cevabi yazarken
gecis yolunun kendisinin bozuk oldugu cikti - hem de kurulumun ilk
gununden beri.

| Nerede | Ne oluyordu |
|--------|-------------|
| `kurulum.sh` | Kasa ve bilgi deposu **kosulsuz** kopyalaniyordu. Herkese acik surumde bu iki klasor YOK; `cp` hata veriyor, `set -e` kurulumu oracikta kesiyordu. Eklenti **hic kopyalanmadan** cikiliyordu. |
| `guncelle.sh` | `git pull origin master` yaziliydi. Acik depo `main` dalinda; guncelleme oradan hic gelmiyordu. |
| `kurulum.ps1` | Kurulu `CLAUDE.md` yedeksiz eziliyordu. Kullanici kendi kurallarini oraya islediyse geri getirilemiyordu. |

Ilki yalniz ilk kurulumu degil, **her guncellemeyi** vuruyordu: `/guncelle`
ikinci adimda `kurulum.sh`'i cagirir. Yani Mac ve Linux'ta tek komutla
guncelleme de ayni yerde kesiliyordu. Windows tarafi ayni durumu zaten
"atlandi (kaynak yok)" deyip gecmisti - iki isletim sistemi ayni betigin
iki farkli davranisini yasiyordu.

**Duzeltmeler:**

- `kurulum.sh` eksik kaynagi atlar, durmaz. Windows ile ayni davranis.
- `guncelle.sh` dal adi yazmaz, takip edilen dali ceker (`--ff-only`).
  Kendi kopyalama listesini de tutmaz; `kurulum.sh`'i cagirir. Iki liste
  zamanla ayrisinca guncelleme, kurulumun duzelttigi hatalari geri
  getiriyordu.
- Kurallar dosyasi uzerine yazilmadan once yedeklenir:
  `~/.claude/enver/yedek/CLAUDE.<tarih>-<saat>.md`. Yedek yalniz icerik
  gercekten farkliysa alinir; ayni dosya icin cop uretilmez.
- Yedek karsilastirmasi `Get-FileHash` yerine .NET ile yapilir. Kilitli
  bir makinede o cmdlet bulunamadi ve kurulum tam yedek adiminda hata
  verip durdu - bu, senaryo yazilirken canli olarak yakalandi.

**Belge:** Iki kurulum kilavuzuna da "Eski surumden gecis" bolumu
eklendi. Orada soylenmesi gereken sey su: `/guncelle` **2.13.0'da geldi**.
Daha eskisinde ne komut ne de klonun yerini tutan
`~/.claude/enver/kurulum-bilgisi.json` vardir; komut klonu bulamaz. Ilk
gecis elle yapilir, sonrasi tek komuttur.

**Olcum:** `kurulum-testleri.py` - 24 senaryo. Kurulum gercekten
calistirilir ama kum havuzunda: `HOME` (ve Windows'ta `USERPROFILE`)
gecici dizine cevrilir, gercek `~/.claude` dokunulmadan kalir. Kasa ve
bilgi deposu olmayan bir kaynak agaci kurulur - yani acik surumdeki
durum - ve eklentinin gercekten kopyalandigi gorulur. Takime baglandi.

## 3.3.2 — Iki dillilik komut belgelerinin otesine gecti

"Her seyin Ingilizcesi olsun" denince olculdu: komut belgelerinin 30'u da
iki dilliydi ama **15 belge tek dilli kalmisti** ve bunu hicbir kontrol
olcmuyordu.

| Nerede | Kac dosya |
|--------|-----------|
| Ajanlar | 5 |
| Beceriler | 4 |
| Sablonlar | 4 |
| Kural belgesi (`references/kurallar.md`) | 1 |
| Ornek kurallar (`CLAUDE.ornek.md`) | 1 |

Hepsine Ingilizce bolum yazildi. Ajan ve beceri bolumleri ne yaptigini
degil **nasil davrandigini** anlatiyor: devralma ajani "buldugunu
raporlar, varsaydigini degil", guvenlik ajani "sir degerini yazmaz, yalniz
dosya ve satiri", kesif becerisi "kesif bitmeden kodlama yok".

**Kasa bolumu tamamlandi.** Kilavuzda gunluk kullanim vardi ama sunlar
yoktu: ilk kurulumun nasil yapildigi, duz metin kaynagin arsivlenmesi
gerektigi, kasanin MAKINEYE OZEL oldugu (`kasa/` senkron olmaz, her
bilgisayarda ayri kurulur) ve parola unutulursa ne olacagi. Ingilizce
bolumde ayrica `liste` ve `yaz` komutlari ile uyarilar eksikti.

**Kapiya baglandi.** Faz 10 artik ajan, beceri, sablon ve kural
belgelerinde de Ingilizce bolum ariyor. Yeni bir ajan ya da beceri tek
dilli eklenirse takim kalir.

Tam takim: **587 gecti, 0 kaldi** (cikis kodu 0).

## 3.3.1 — Kasa kontrolu yazdiriyordu, olcmuyordu

3.3.0'da eklenen gerileme kontrolu kasanin boyutunu **yazdiriyor** ama
karsilastirma yapmiyordu; kontrol her kosuda kosulsuz geciyordu. Yani
kasa yeniden ezilse bile takim "gecti" derdi.

Olcmeyen bir kontrol, kontrol degildir - bugun bunun uc ornegi cikti
(kosucunun kalan bolumu saymamasi, panelin kendi menusunu yanlis
saymasi, ve bu).

Artik kasa bolumunun basinda dosyanin boyut ve zaman damgasi alinip
bolum sonunda karsilastiriliyor. Kasa icerigi hicbir yerde okunmaz;
yalniz ust veriye bakilir.

**Gercek kasayla dogrulandi:** kullanicinin kasasi arsivdeki kaynaktan
geri yuklendi (3 dosya, 1846 bayt), test parolasi artik acmiyor, ve tam
takim kosusundan sonra dosya birebir ayni kaldi.

Tam takim: **586 gecti, 0 kaldi** (cikis kodu 0).

## 3.3.0 — Kapi testi kullanicinin sifre kasasini eziyordu

Bugunku en agir bulgu. Kasa 21 Temmuz'da kurulmus, parola girilmis, duz
metin kaynagi arsive alinmisti. Ama **her tam takim kosusunda gercek kasa
siliniyor, yerine test kasasi yaziliyordu.**

`faz2-kapi.sh` kasa motorunu denerken sunu cagiriyordu:

```
kasa.py kur --kaynak _calisma/kasa-testi --parola "KapiTesti2026!" --uzerine-yaz
```

Kasa yolu `proje_kok()` ile cozuluyor ve teste kum havuzu baglanmamisti;
`--uzerine-yaz` bayragi da soru sormadan degistiriyordu. Sonuc: kullanici
kendi parolasiyla kasasini acamaz hale geliyordu, cunku dosya artik
testin 13 karakterlik icerigini ve testin parolasini tasiyordu.

**Nasil ortaya cikti:** "kasayi ne icin kuracagiz" sorusu soruldu. Durumu
olcerken kasanin zaten kurulu oldugu, ama dosyanin 162 bayt oldugu ve
bugun degistigi goruldu. Test parolasiyla acildi: icinde yalniz `a.md`
vardi.

**Veri kaybi yok.** Duz metin kaynagi 21 Temmuz'da arsivlenmisti; "hicbir
veri silinmez" kurali bu kez gercekten ise yaradi.

**Duzeltme:** kasa testleri kum havuzunda kosuyor (3.1.2'de hafiza icin
yapilan yonlendirmenin ayni). Ayrica gerileme kontrolu eklendi: test
sirasinda gercek kasa dosyasina dokunulmadigi olculuyor.

Bu, hafiza kirlenmesiyle ayni sinifin en agir ornegi. Testin gercek
durumu degistirmesi orada gurultu uretiyordu; burada kullanicinin
sifrelerini goturuyordu.

Tam takim: **586 gecti, 0 kaldi** (cikis kodu 0).

## 3.2.9 — Depo sayfasinin tamami iki dilli

Onceki iki surumde basliklar ve iki tablo iki dilli olmustu, ama sayfanin
**govde metinleri** hala tek dildi: "Neden var" altindaki cumleler,
kurulum adimlarinin aciklamalari, uyarlama bolumu, test ve katki
paragraflari yalniz Turkce yaziliydi. Yabanci okur basligi anliyor,
altindaki cumleyi anlamiyordu.

README bastan yazildi: **her Turkce paragrafin altinda Ingilizcesi var**,
her tablo iki dilli, her baglantinin Ingilizce karsiligi yaninda.

- "Neden var" ve "Uyarlama" tablolari cift dilli hale getirildi (satir
  ici `<br>` ile, tek tablo iki dil).
- Akis semasindaki kutu adlari iki dilli yazildi.
- "Tam liste" gibi tek dilli baglantilarin yanina Ingilizce karsiligi
  kondu.
- Kurulum bolumune iki not eklendi: kisa komut adi cozulmezse ad alanli
  bicim, ve macOS'ta `python` yerine `python3`.
- Koruma bolumundeki eski bilgi duzeltildi: kancalar artik
  `.claude/settings.json` ile degil eklentinin `hooks.json` dosyasiyla
  devreye giriyor (3.0.0'dan beri boyle).

Tam takim: **585 gecti, 0 kaldi** (cikis kodu 0).

## 3.2.8 — "Ne yapar" sutunlari da iki dilli, sayilar olculuyor

Basliklar 3.2.7'de iki dilli olmustu ama tablolarin **icerigi** hala tek
dildi: komut ve koruma tablolarinin "Ne yapar" sutunu yalniz Turkceydi.
Yabanci okur basligi anliyor, satiri anlamiyordu.

- Komut tablosuna ve koruma tablosuna **"What it does" sutunu** eklendi.
  Her satir iki dilde okunuyor.
- Iki tabloda eksik satirlar da tamamlandi: `/proje-devral` (3.1.0'in
  ana yeniligi) komut tablosunda yoktu, `iz-kontrol.py` koruma
  tablosunda yoktu.

**Bilesen sayilari yanlistı.** README "29 komut, 3 beceri, 4 ajan, 48
betik" diyordu; gercek **30 komut, 4 beceri, 5 ajan, 53 betik**. Bu, bugun
ucuncu kez kayan sayi (once 27 komut, sonra 105 senaryo, simdi bu).

Elle yazilan sayi eskir. Bu yuzden **kapiya baglandi**: Faz 10 artik
dizinleri sayip README'deki degerle karsilastiriyor. Bir bilesen eklenip
README guncellenmezse takim kaliyor.

Tam takim: **585 gecti, 0 kaldi** (cikis kodu 0).

## 3.2.7 — Depo sayfasi iki dilde taranabiliyor

3.2.5'te Ingilizce ozet blogu eklenmisti ama sayfanin govdesi hala tek
dildi: **Neden var, Kurulum, Kilavuzlar, Icinde ne var, Korumalar, Nasil
calisir, Uyarlama, Test, Katki, Lisans** - hepsi Turkce basliklardi.
Yabanci okur, ozet blogunu gecince yine Turkce duvara carpiyordu.

Icerik zaten vardi: `README.en.md` tam bir ayna. Eksik olan **isaret**ti.

- Iki README'de de basliklar cift dilli: `## Neden var - Why it exists`,
  `## Kurulum - Install` ... Boylece sayfa hangi dilde bakilirsa bakilsin
  taranabiliyor, okur aradigi bolumu bulup Ingilizce belgeye geciyor.
- Kilavuz tablosu iki sutunlu oldu: her belgenin Turkcesi ve Ingilizcesi
  yan yana. Once yalniz Turkce satirlar vardi, Ingilizce belgeler
  sayfadan gorunmuyordu.
- Depo aciklamasi (About) Ingilizce yazildi; arama sonuclarinda ve sayfa
  basliginda gorunen metin artik Ingilizce basliyor.

Neden onemli: acik kaynak bir is okunmadan degerlendirilmez. Sayfa,
okurun dilinde bir tutamak vermiyorsa icerigin tam olmasi kimseye
ulasmaz.

Tam takim: **584 gecti, 0 kaldi** (cikis kodu 0).

## 3.2.6 — Yol denetimi kendi belgemdeki hatayi yakaladi

3.2.5'te README'ye eklenen Ingilizce blokta dil dosyasinin yolu eksik
yazilmisti: `diller/en.json` denmisti, dogrusu
`plugins/enver-framework/diller/en.json`. Yani yeni gelen kullaniciya var
olmayan bir yol gosteriliyordu.

Yol denetimi bunu yakaladi ama **surum yine de yayinlandi**: takim
"KALAN VAR" derken cikis kodu boru hattinda maskelenmisti. Ders, kapinin
kendisiyle ilgili: bir kapi ancak cikis koduna bakilirsa kapidir.

Yol duzeltildi, tam takim cikis koduyla birlikte dogrulandi.

Tam takim: **584 gecti, 0 kaldi** (cikis kodu 0).

## 3.2.5 — Depo sayfasi yabanciya kendini anlatiyor

Depo herkese acik ve MIT lisansli, ama github.com sayfasinda **ilk ekranda
tek satir Ingilizce yoktu**. Dil cubugu vardi (`Turkce - English`) fakat
kucuk bir baglantiydi; Turkce basliklari goren biri o baglantiyi fark
etmeden sayfayi kapatirdi.

README'nin en ustune, rozetlerin hemen altina **Ingilizce ozet blogu**
kondu: bunun ne oldugu, ne yaptigi, lisansi ve dort belgeye dogrudan
baglanti. Ayrica arayuzun varsayilan dilinin Turkce oldugu ama dil
katmaninda Ingilizce bulundugu acikca yaziliyor - kuran kisi surprizle
karsilasmasin.

Neden onemli: acik kaynak bir is, okunmadan degerlendirilmez. Ilk on
saniyede "bu benim isime yarar mi" sorusuna cevap vermeyen sayfa kapanir.

Tam takim: **584 gecti, 0 kaldi.**

## 3.2.4 — Takim "hepsi gecti" derken bir bolum kalmisti

Guncelleme bildirimi ikinci bilgisayarda ucdan uca denenirken uc hata
birden cikti. Ucu de ayni koke bagli: **olcum, olctugunu sandigi seyi
olcmuyordu.**

### 1. Bildirim bu kez hic cikmadi

3.2.2'de yanlis uyari kapatilmisti; simdi ters yon acildi. Onbellekteki
uzak surum eskiyince yeni yayin bir gun boyunca **hic** soylenmiyordu.

Duzeltme: yerel surum onbellek yazildigindan beri degistiyse (yani
guncelleme yapilmissa) kayitli uzak deger de eskimis olabilir - onbellek
atlanip aga bir kez bakiliyor. Ag yoksa kayitli karar oldugu gibi
donmuyor, uzak surum ile canli yerel surum yeniden karsilastiriliyor.

### 2. Senaryo takimi calisiyor ama SAYILMIYORDU

Kosucu sonuc satirini yalniz tam Turkce bicimde ariyordu
("N gecti, M kaldi" ASCII yazilmissa okuyamiyordu). Iz senaryolari
3.2.0'da yeniden yazilirken ASCII'ye donmustu; o gunden beri **24 senaryo
kosuyor ama toplama girmiyordu**.

Daha once bu dususu fark edip "senaryolarin birlesmesinden" diye
aciklamistim - yanlisti. Sebep buymus.

### 3. Kalan bolum kosuyu DUSURMUYORDU

Daha kotusu: sonuc satiri okunamayinca bolum `[KALDI]` yazdiriyor ama
`TOPLAM_KALAN`'a eklenmiyordu. Ekranda iki satir "KALDI" gorunurken
sonuc **"HEPSI GECTI, 0 kaldi"** diyordu.

Bir kapi, kapali oldugunu bildigi halde "gecti" diyorsa kapi degildir.
Artik: sonuc satiri okunamayan takim bozuk sayilir, cikis kodu sifirdan
farkliysa kalan sayilir, iki yazim bicimi de okunur.

### Yeni senaryo takimi: guncelleme-testleri.py (7 senaryo)

Bildirim iki yonde de yanilabilir ve ikisi de kullaniciyi yaniltir:
yanlis uyari ("guncelledim ama hala soyluyor") ve sessiz kalma ("yeni
surum var ama demiyor"). Yedi senaryo ikisini de olcuyor; ag gerekmez.

Tam takim: **584 gecti, 0 kaldi** (onceki 553 sayimi eksikti).

## 3.2.3 — Panel kendi menusunu yanlis sayiyordu

`/panel` kendini "4 sekme, 16 kategori, **80+ islem**" diye tanitiyordu.
Menunun kendisi sayildi: sekme ve kategori dogru, islem sayisi degil.

| Olculen | Aciklamada | Gercek |
|---------|------------|--------|
| Sekme | 4 | 4 |
| Kategori | 16 | 16 |
| Alt islem | 80+ | **58** |

Kucuk bir fark ama ayni sinifin ornegi: belge, gercegin bir adim onunde
yuruyordu. Sayilar artik menunun kendisinden olculuyor.

**Not:** 30 egik cizgi komutu ile panelin 58 islemi ayri seylerdir. "Kac
komut var" sorusunun cevabi 30; "kac islem yapabilirim" sorusununki daha
fazla, cunku panel tek basina bir menu katmani.

Tam takim: **553 gecti, 0 kaldi.**

## 3.2.2 — Güncelleme bildirimi güncelledikten sonra geçmiyordu

İkinci bilgisayarda güncelleme akışı uçtan uca denendi. Bildirim doğru
çıktı, `/guncelle` çalıştı, klon 3.2.1'e geldi — ama açılış brifingi hâlâ
**"GÜNCELLEME VAR: 3.2.0 → 3.2.1"** diyordu.

**Sebep:** güncelleme durumu günde bir ağ yokluyor, arası önbellekten
okunuyordu. Önbellek yalnız uzak sürümü değil **yerel sürümü de**
hatırlıyordu. Güncelledikten sonra yerel sürüm değişiyor ama önbellek bir
gün boyunca eskisini söylüyordu.

`guncelleme.py yap` önbelleği siliyordu, ama kabuk betiği (`guncelle.ps1`
/ `guncelle.sh`) silmiyordu; o yoldan güncelleyen kullanıcı bir gün
boyunca yanlış bildirim görüyordu — ve güncellemenin işe yaramadığını
sanıyordu.

**Düzeltme:** yerel sürüm artık hiç önbelleğe alınmıyor, her seferinde
dosyadan okunuyor. Ağ gerektiren şey uzak sürümdür; yerel sürüm anında
ölçülebilir. **Ölçülebilen bir şey önbellekten okunmaz** — bu, bugün
düzeltilen yedinci hatanın da ortak dersiydi.

Gerileme kontrolü eklendi: bildirim mantığı yerel sürümü canlı ölçmezse
takım kalır.

Tam takım: **553 geçti, 0 kaldı.**

## 3.2.1 — Her şey iki dilli

Çerçeve herkese açık bir depoda duruyor ama belgelerin çoğu tek dilliydi:
yalnız README'nin İngilizcesi vardı. Dışarıdan gelen biri kurulumu okuyup
kılavuza geçtiğinde Türkçe duvara çarpıyordu.

**Eklenen belgeler:**

| Belge | Ne |
|-------|-----|
| `KURULUM-KILAVUZU.en.md` | Kurulum kılavuzunun tamamı |
| `KULLANIM-KILAVUZU.en.md` | Kullanım kılavuzunun tamamı |
| `DEGISIKLIKLER.en.md` | Sürüm geçmişi (3.0.0'dan bugüne) |

Türkçe belgeler İngilizcesine, İngilizceler Türkçesine bağlanıyor; hangi
dilde açarsan aç diğerine bir tıkla geçiliyor.

**30 komut belgesinin hepsine İngilizce bölüm eklendi.** Komutun ne yaptığı
ve nasıl çağrıldığı artık iki dilde yazılı — ad alanlı biçim de dahil.

**Kapıya bağlandı (11 yeni kontrol).** İki dillilik artık bir niyet değil
ölçüm: dört belgenin iki dili de var mı, karşılıklı bağlar duruyor mu, 30
komutta İngilizce bölüm var mı, `tr.json` ile `en.json` aynı anahtarları
mı taşıyor. Biri tek dilli kalırsa Faz 10 kapısı kapanır.

**Sürüm notları da iki dilli yayınlanıyor** — bugüne kadar yalnız Türkçe
yazılıyordu.

Tam takım: **552 geçti, 0 kaldı.**

## 3.2.0 — İz kuralı kod yorumlarına daraltıldı

**Kural değişti (Enver'in kararı).** Araç izi yasağı artık yalnız **kod
yorum satırlarını** kapsıyor. Belge, düz metin, dize değeri, komut ve yol
serbest.

**Neden:** eski kural dosyanın tamamını tarıyordu ve çalışmayı sürekli
kesiyordu. Bir kurulum komutu, bir dosya yolu, bir belge cümlesi, hatta
test verisinin kendisi uyarı üretiyordu. Bugün tek oturumda dört kez
yanlış öttü. Sürekli yanlış uyaran bir denetim okunmaz hale gelir ve asıl
yakalaması gereken satırı da o gürültünün içinde kaçırır.

Geriye kalan kural nettir ve savunulabilir: teslim edilen kaynak kodun
yorum satırlarında üretici izi bulunmaz. Yorum, kodu yazanın sesidir;
orada başka bir ad geçmez.

**Ne yapıldı:**

- `iz-kontrol.py` artık dosyayı yorum yorum tarıyor. 30'dan fazla uzantı
  için yorum biçimi tanımlı: `#`, `//`, `/* */`, `<!-- -->`, `--`, `<# #>`.
  Blok yorumları satırlar arasında takip ediliyor.
- Muafiyet mantığı korundu: bir yorum kurulum komutunu ya da dosya yolunu
  anlatıyorsa iz sayılmaz. Aynı yorumda hem yol hem üretici ifadesi varsa
  yine uyarır.
- Basit bir tarayıcıdır; dize içindeki `//` gibi durumları ayırt etmez.
  Bu yönde yanılırsa **fazla** yakalar, az değil — iz denetiminde güvenli
  taraf budur.
- `devral.py` aynı ayıklayıcıyı kancadan alıyor. Devralma taraması ile
  denetim tek tanımı paylaşır, ayrı düşemezler.
- Senaryolar baştan yazıldı: 18 → **24**. Sekizi yorumdaki izi yakalıyor
  (Python, JavaScript, PHP iki biçim, CSS, HTML, SQL), altısı yorum dışı
  kullanımın artık serbest olduğunu ölçüyor, altısı kurulum biçimlerinin
  yorumda bile sessiz kaldığını.
- `CLAUDE.md`, `CLAUDE.ornek.md` ve `references/kurallar.md` yeni kuralı
  anlatıyor. Commit yazarlığı kuralı ayrı ve yerinde duruyor: yazar Enver
  KOCAK'tır, ortak yazar eklenmez.

### İkinci bilgisayarda ölçüm

Çerçeve ikinci bir makineye (SSH ile, sıfırdan kurulum) kuruldu ve **30
komutun 30'u** çözüldü. Ama kısa ad çalışmıyor: `/panel` orada
`Unknown command` veriyor, `/enver-framework:panel` çalışıyor. Aynı sürüm,
aynı eklenti, aynı ayar — farkın kaynağı bulunamadı.

Kılavuzlara ad alanlı biçim eklendi. Yeni kuran biri kısa adı deneyip
"çalışmıyor" demesin diye; ölçülen gerçek yazıldı, tahmin değil.

Tam takım: **540 geçti, 0 kaldı.** Senaryo toplamı 127.

## 3.1.7 — Sağlık kontrolü temiz kurulumu hasta sanıyordu

Çerçeve ilk kez **ikinci bir bilgisayara** kuruldu (SSH ile, sıfırdan:
VS Code, Python, git, Node, Claude Code, sonra eklenti). Kurulum sorunsuz
geçti, kapı testleri temiz klonda 160/0 verdi. Ama sağlık kontrolü
**2 BOZUK** bildirdi ve ikisi de yanlış alarmdı.

**"Ayar dosyası yok - hiçbir koruma çalışmıyor olabilir".** Denetim
korumaları `.claude/settings.json` içinde arıyordu. Oysa 3.0.0'dan beri
kancalar eklentinin `hooks.json` dosyasıyla geliyor; kurulum betiği
bilerek kayıt yapmıyor (çift çalışmasın diye). Yani eklentiyi kuran
**her normal kullanıcıya** bu uyarı çıkıyordu - hem de "çerçeve gerçekten
çalışıyor mu" sorusunu cevaplamakla görevli araçta. En kötü yanlış alarm
budur: doğru kurulmuş bir sistemi bozuk gösterir.

Denetim artık iki geçerli yolu da tanıyor: eklenti kurulumu ya da çalışma
ağacı kaydı. Kancaların hangi kopyadan çalıştığı da düzeltildi - ölçüm
gerçekten çalışan kopyaya sorulur (`CLAUDE_PLUGIN_ROOT`, sonra çalışma
ağacı, sonra eklenti önbelleği). "Kayıtlı" ile "çalışıyor" ayrı şeylerdir;
eklenti yolu bulunduğunda da altı koruma ölçümü yine koşar.

**"Ham günlük depoya giriyor".** `git check-ignore -q gunluk` çağrılıyordu.
Klasör henüz oluşmamışsa git `gunluk` adını dizin saymaz ve `/gunluk/`
deseni eşleşmez - taze kurulumda daima yanlış "bozuk". Eğik çizgi eklendi
(`gunluk/`), aynısı `hafiza/` için de yapıldı. Ölçülen şey klasörün
varlığı değil kuralın kendisidir.

**Neden ikisi de aynı hikâye:** denetim, sistemin bugünkü gerçeğinden
kopmuştu. Biri eski kurulum biçimini arıyordu, diğeri henüz var olmayan
bir klasörü. Sürekli yanlış öten bir sağlık kontrolü, gerçekten bozuk
olduğu günü de kaçırır.

Ölçüm (terminal1, temiz kurulum): kapı testleri **160 geçti, 0 kaldı**.

## 3.1.6 — Kapı testleri tek makineye bağlı kalmaktan çıktı

Çerçeve ikinci bir bilgisayarda denenecekti. Denemeden önce testler
tarandı: **motorun kendisinde sabit yol yok** - kancalar, betikler ve
hafıza katmanı yolu `proje_kok()` üzerinden çözüyor. Ama testlerin kendisi
geliştirme makinesine bağlıydı; başka bir makinede kırmızı yanan kapılar,
gerçek hatayla karıştırılırdı.

**Yorumlayıcı adı varsayılıyordu.** 241 çağrının hepsi `python` diyordu.
macOS'ta o komut çoğu kurulumda yoktur, yalnız `python3` bulunur - takım
orada toptan çökerdi. Yorumlayıcı artık her betiğin başında bir kez
çözülüyor.

Seçim sırasında **adayın var olması yeterli sayılmıyor, çalışması
gerekiyor.** Bu düzeltme yazılırken ortaya çıktı: bu makinede `python3`
adıyla Microsoft Store kısayolu geliyor, `command -v` onu buluyor ama
çalıştırılınca "Python was not found" diyor. İlk sürüm tam bu yüzden 285
kontrolü düşürdü - takım kendi düzeltmesindeki hatayı yakaladı.

**Müşteri projesi denemesi sabit sürücü yolundaydı.** Faz 0, muafiyet
işareti taşımayan bir depoda izin yakalandığını ölçmek için
`D:/Projeler/_test-musteri` açıyordu. Artık sistemin geçici dizini
kullanılıyor; yol, kabuğun ve Python'un aynı çözeceği biçime getiriliyor.

**Tarama kökü testi makineye bakıyordu.** Faz 4, kökün `D:/Projeler`
olmasını bekliyordu. Oysa ölçülmesi gereken **kural**: tarama serbest
dolaşmaz, tanımlı köklerle sınırlıdır. Kök makineye göre değişir ve ayar
dosyasında durur. Test artık kuralı ölçüyor: kök tanımlı mı, gerçekten
var mı, dosya sisteminin kökü değil mi, bütün projeler onun altında mı.

**CI iki işletim sisteminde koşuyor.** `windows-latest` yanına
`macos-latest` eklendi. Taşınabilirlik iddiası ancak ölçülürse doğrudur;
artık her push'ta yeniden sorulacak.

Tam takım (Windows): **562 geçti, 0 kaldı.**

## 3.1.5 — Temizlik kaynağa inmeyince kalıcı olmuyordu

3.1.2'de hafıza test artığından temizlenmişti. Bu sürümde ilk oturum özeti
çıkarıldı ve **artık geri geldi** - sızıntı kapısı yakaladı. Temizlik
belirtiyi almış, kaynağı bırakmıştı.

**Ham günlük hafızayı besler.** `hafiza/` temizlendi ama oturum özeti
`gunluk/komutlar.jsonl` dosyasından üretilir; oradaki 104 test kaydı ilk
özette hafızaya geri döndü. `artik-temizle.py` artık ham günlüğü de
ayıklıyor, `sizinti-kontrol.py` de onu denetliyor. Depoya girmeyen bir
dosya, depoya giren dosyayı üretiyorsa denetim dışı kalamaz.

**Ham günlük hiç döndürülmüyordu.** `oturum.py bitir` günlüğü yalnız
`--gunlugu-temizle` verilirse arşivliyordu; kimse vermiyordu. Sonuç: her
özet **bütün geçmişi** yeniden özetliyordu. Bugünkü özet 21 Temmuz'dan
başlıyor, 165 komut ve 131 dosya sayıyordu - yani "bu oturumda ne oldu"
sorusuna cevap vermiyordu, üstelik aynı satırlar her oturumda tekrar
ediyordu.

Günlük artık **varsayılan olarak** döndürülüyor: özet çıkarıldıktan sonra
`komutlar-<tarih>-<sıra>.jsonl` adıyla arşivleniyor. Silme yok. Birikmeli
özet isteyen `--gunlugu-birak` diyebilir.

**Neden önemliydi:** hafıza katmanının tek işi "nerede kaldık" sorusuna
doğru cevap vermek. Her oturumda aynı dört günlük özeti gören kişi bir
süre sonra o belgeyi hiç okumaz.

İki gerileme kontrolü eklendi: günlük özetten sonra dönüyor mu, dönen
günlük siliniyor mu arşivleniyor mu.

Tam takım: **562 geçti, 0 kaldı.**

## 3.1.4 — Durum satırı jeton sayıyor, iz denetimi yolu iz sanmıyor

Bütünlük denetimi çalıştırıldı: belgelerin işaret ettiği her betik yolu,
komutların çağırdığı her dosya, bütün betiklerin sözdizimi, bütün kayıt
dosyalarının geçerliliği ve ayarlardaki kanca yolları tarandı — **kırık
bağlantı yok**. Ama üç davranış hatası çıktı.

**Dosya yolu iz sayılıyordu.** Çerçevenin çalışma deposu `enver-claude-...`
adını taşıyor; mutlak yol yazan her betik ve her kurulum belgesi bu adı
geçirmek zorunda. İz denetimi bunlara ötüyordu. 3.1.1'in kararı açıktı —
"muafiyet yalnız makine biçimlerini kapsar: yol, ortam değişkeni, komut,
paket adı, adres" — ama desen yol içindeki klasör adını kapsamıyordu.

Muafiyet **eğik çizgi şartıyla** eklendi: "claude" ya bir yol parçasından
sonra ya da öncesinde gelmeli. Boşluk yol deseninde yer almadığı için düz
metindeki ürün adı muafiyete giremez — aynı satırda yol bulunsa bile.
Dört senaryo eklendi (üçü sessiz kalmalı, biri yol + üretici ifadesi aynı
satırda: yine uyarmalı). İz senaryoları 18 → 22.

**Durum satırı maliyet yerine jeton gösteriyor.** Dolar tutarı, harcamayı
anlatıyordu ama iş sırasında asıl merak edilen tüketim ve bağlam doluluğu.

Gösterilen sayı **yeni işlenen** jetondur: girdi + önbelleğe yazılan +
üretilen. Önbellek okuması **bilerek sayılmaz** — ölçüldü: bir oturumda
74,5 milyon jetonluk önbellek okuması, 1,4 milyonluk gerçek tüketime
karşılık geliyordu. "76M" yazan bir sayaç doğru değil yanıltıcıdır; aynı
bağlamı her turda yeniden sayar.

Bağlam ayrı gösterilir — "ne kadar harcadım" ile "ne kadar doldu" farklı
sorulardır:

```
enver-claude-framework · OFIS-PC · 12 faz bitti · kasa kilitli · 1.4M jeton (bağlam 318k)
```

Sayım **artımlıdır**: oturum kaydı büyüyen bir günlüktür, her çizimde
baştan okunsa durum satırı yavaşlar. Son okunan konum ve toplam saklanır,
yalnız yeni satırlar işlenir.

**Faz göstergesi sessizce boşalmıştı.** Gösterge fazı bir belgedeki
"Siradaki:" başlığından okuyordu; 3.1.2'de o başlık kaldırılınca gösterge
hiçbir şey yazmaz oldu ve kimse fark etmedi. Faz planı belgede değil
motorun kaydında durur: artık `hafiza/faz-plani.json` okunuyor, hepsi
bitmişse "12 faz bitti" yazıyor. Gerileme kontrolü eklendi.

**Neden bu üçü aynı hikâye:** bir gösterge ya da denetim, ölçtüğü şeyin
gerçek kaynağından koparsa sessizce yanlışa döner. Yanlış öten denetim
okunmaz olur, boşalan gösterge fark edilmez, yanıltıcı sayaç yanlış karar
verdirir.

Tam takım: **560 geçti, 0 kaldı.**

## 3.1.3 — Sanal deneme ölü kancalara soruyordu

3.1.2 yayınlandıktan sonra eklentinin kendisi denetlendi ve **ölü bir kopya**
bulundu. Bulgu ikinci bir hatayı da ortaya çıkardı; ikisi de aynı kökten:
bir dosyanın iki kopyası varsa er geç sessizce ayrışır.

**Depo kökündeki `hooks/` klasörü 3.0.0'dan kalma ölü kopyaydı.** Kancalar o
sürümde eklentinin içine taşınmıştı; kurulum betikleri, ayarlar ve testler
o günden beri `plugins/enver-framework/hooks/` okuyor. Kök kopyası kimsenin
okumadığı halde durdu ve **ayrıştı**: `iz-kontrol.py` orada 3.1.1'in bağlam
düzeltmesini hiç almamış eski sürümdeydi. Klasör arşive alındı, ana dizin
beyaz listesinden çıkarıldı — biri tekrar oraya kopya koyarsa Faz 0 kapısı
artık yakalar.

**Asıl hata bu kopyanın kullanıldığı yerde çıktı.** `kuru-deneme.py` (sanal
deneme, `/kuru-deneme`) kancaları arıyordu ve baktığı iki yerin **ikisi de
depo kökü**ydü. Yani T61'in sözü — "tahmin yürütmez, gerçek korumalara
sorar, rapor ile gerçek davranış ayrılamaz" — aylardır tutmuyordu: rapor
eski kopyanın kararını gösteriyordu.

Arama sırası düzeltildi ve gerçekte çalışan kopyayı sorar hale getirildi:

1. `CLAUDE_PLUGIN_ROOT/hooks` — eklenti olarak kuruluysa çalışan kopya
2. `plugins/enver-framework/hooks` — çalışma ağacındaki eklenti gövdesi

**Neden önemliydi:** yanlış rapor veren bir güvenlik aracı, hiç olmamasından
daha kötüdür — "engel yok" diyen bir rapora güvenip komutu çalıştırırsın.
Ölü kopya kaldırılınca hata kendini gösterdi; bir kopyayı **silmek**,
senkron tutmaya çalışmaktan daha sağlam bir çözümdür.

**Belge düzeltmesi:** `KURULUM-KILAVUZU.md` klasör ağacı hâlâ kök `hooks/`
gösteriyordu; kancalar artık eklentinin içinde, `hooks.json` ile devreye
giriyor.

Tam takım: **553 geçti, 0 kaldı.**

## 3.1.2 — Kapı testleri gerçek hafızaya yazmayı bıraktı

Çerçevenin kendi hafızası, kendi testlerinin çöpüyle dolmuştu. Açılış
brifingi "nerede kaldık" sorusuna otuz kere **"Kapi testi olayi"** diye
cevap veriyordu; gerçek üç iş o gürültünün altında görünmez olmuştu.

**Ölçülen kirlilik:**

| Dosya | Toplam | Test artığı |
|-------|--------|-------------|
| `hafiza/gorevler.json` | 393 kayıt | **390** |
| `hafiza/cihaz-envanteri.json` | 124 cihaz | **124** (hepsi) |
| `hafiza/durum.md` | 1513 satır | **772** |
| `hafiza/hatalar.md` | 1234 satır | 101 blok |
| `hafiza/kararlar.md` | 880 satır | 101 blok |

**Kum havuzu (`testler/_kumhavuzu.sh`).** Hafıza betiklerinin tamamı yolu
`yollar.proje_kok()` üzerinden çözer, o da `CLAUDE_PROJECT_DIR` değişkenini
tanır. Yazan kontroller artık bu değişkenle çağrılıyor; kayıt gerçek
hafızaya değil `_calisma/kapi-kumhavuzu/<zaman>/` altına düşüyor. Havuzun
içine bir `.claude` işareti konur, böylece kök arama yukarı çıkıp gerçek
depoyu bulmaz.

Yalnız **yazan** kontroller yönlendirildi. Gerçek depoyu okuyanlar (dosya
var mı, git yok sayıyor mu, sertifika taraması) olduğu gibi kaldı — yoksa
test ölçmesi gereken şeyi ölçmez. Faz 3, 8 ve 9 düzeltildi.

**`sizinti-kontrol.py` eklendi.** Düzeltmenin bozulmadığını ölçer, Faz 3
kapısına bağlandı. Aranan şey "kapı testi" ifadesi **değil**, testlerin
kullandığı kayıt imzalarıdır: gerçek bir oturum özeti "kapı testleri geçti"
diye yazabilir, bu ihlal değildir. Aynı keskinlik ilkesi 3.1.1'de iz
denetimine, ondan önce yazım denetimine uygulanmıştı.

**`artik-temizle.py` eklendi.** Birikmiş artığı ayıkladı: 20 dosya
düzeltildi, tamamı test verisi olan 1 dosya arşive taşındı. Silme yok —
ayıklamadan önce hafızanın tamamının kopyası
`_arsiv/2026-07-25_hafiza-kapi-testi-artiklari/` altına alındı. Test
imzaları tek yerde tanımlı (`sizinti-kontrol.py`); denetim ile temizlik
aynı listeyi okur, birbirinden ayrı düşemezler.

**Neden önemliydi:** hafızanın tek işi "nerede kaldık" sorusuna doğru cevap
vermek. Kendi testi yüzünden yanlış cevap veren bir hafıza, hiç olmamasından
daha kötüdür — okuyan kişi yanlış yerden devam eder. Aynı sebeple bir
oturum özetine test dizesi karışması Faz 5'te de yaşanmıştı; kum havuzu o
hata sınıfını kökünden kapatıyor.

**Bilinen ve kabul edilen:** `deploy.py kontrol` ile sertifika taraması hâlâ
gerçek hafızaya yazar. İkisi de gerçek veri üretir, sabit boyuttadır ve
birikmez — yalnız tarih damgası tazelenir.

### Aynı sınıftan iki hata daha

**Test yolu mutlaklaştırılmıyordu.** Beş test betiği kök yolunu
`Path(sys.argv[1])` diye alıyordu. Görece yol verilince (`.`) üst dizin
hesabı kayıyor ve deneme klasörü **ana dizine** düşüyordu; "ana dizin temiz
kalır" kapısı bu yüzden koşu sırasına göre bazen kalıyordu. Yol artık
`.resolve()` ile mutlaklaştırılıyor. Düşmüş klasör arşive alındı.

**İndeks üreteci kendi uyarısını açıklama sanıyordu.** Klasör açıklamasını
alt indeksin ilk `>` satırından okuyordu, o satır da üretecin kendi
"Bu belge otomatik üretilir" uyarısıydı — kök indekste beş klasörün beşi de
aynı cümleyi gösteriyordu. Uyarı satırı artık atlanıyor, klasör açıklamaları
`aciklamalar.json` dosyasından okunuyor.

**Paylaşım kopyasının indeksi kaynağın klasörlerini anlatıyordu.**
`paylasima-hazirla` indeksi kopyalıyordu; açık sürümde bulunmayan `hafiza/`,
`bilgi/` ve `gelistirme-arastirmasi/` klasörleri listede görünüyordu. Depoyu
ilk kez açan kişi olmayan klasörleri arıyordu. İndeks artık **hedefte
yeniden üretiliyor**; üretece bunun için `--kok` seçeneği eklendi.

### Belgeler ölçümle hizalandı

Sayılar elle değil koşudan okundu:

| Belge | Eskiden | Ölçülen |
|-------|---------|---------|
| `KURULUM-KILAVUZU.md` | 27 komut | **30** |
| İki kılavuz | 105 senaryo, 35 saniye | **121 senaryo, 40 saniye** |
| `README.en.md` | 49 scripts | **52** |
| `commands/surum.md` | "altı yeri günceller" | **dokuz** (araç zaten dokuzunu güncelliyordu) |

- **`KULLANIM-KILAVUZU.md`** komut rehberine altı komut eklendi:
  `/faz-kontrol`, `/temizlik`, `/framework-ayarlari`, `/surum`,
  `/dokumantasyon`, `/toplu-islemler`. Kurulu ama kılavuzda yoklardı.
- **`00-DEVAM-BURADAN.md`** hâlâ "Sıradaki: FAZ 6" diyordu, oysa on bir fazın
  tamamı kapanmıştı. Yeni oturumda o belgeyi okuyan yanlış yerden devam
  ederdi. Durum bölümü ölçülen değerlerle yenilendi, kapı testi tablosu
  on iki kapının hepsini gösteriyor.

Tam takım ölçümü: **553 geçti, 0 kaldı, 40 saniye.**

## 3.1.1 — İz denetimi bağlam tanıyor, belgelerdeki eski yollar düzeltildi

İki eski yara kapatıldı. İkisi de aynı türden: denetim ya da belge,
sistemin **gerçekte** nasıl çalıştığından kopmuştu.

**İz denetimi artık kurulumun kendisini iz sanmıyor.** `iz-kontrol.py`
dosyanın tamamında araç adı arıyordu. Ama çerçeve bir eklenti: kurulum
belgesinde `claude plugin install`, ayar yolunda `~/.claude/settings.json`,
kancada `${CLAUDE_PLUGIN_ROOT}` geçmek zorunda. Denetim bunların hepsine
ötüyordu.

- Tarama satır satır yapılıyor; **muaf biçimler satırdan çıkarıldıktan
  sonra** aranıyor. Böylece `claude plugin install ...` sessiz kalıyor,
  aynı satırdaki "generated with ..." yakalanıyor.
- Muafiyet yalnız **makine biçimlerini** kapsıyor: yol, ortam değişkeni,
  komut, paket adı, adres. Düz metinde geçen ürün adı hâlâ ihlal — asıl
  kural odur.
- Uyarı artık satır numarası ve satırın kendisini gösteriyor; "hangi
  ifade" değil "nerede" sorusunun cevabı veriliyor.

**Neden önemliydi:** sürekli yanlış uyaran bir denetim bir süre sonra hiç
okunmaz, ve asıl yakalaması gereken satırı da o gürültünün içinde
kaçırırsın. Aynı ilke `yazim-kontrol.py`'de zaten uygulanmıştı.

- **`iz-testleri.py` eklendi (18 senaryo)** — kancanın testi hiç yoktu.
  Yedi gerçek iz yakalanmalı, sekiz kurulum biçimi sessiz kalmalı, bir
  senaryo da ikisinin aynı satırda olduğu durumu ölçüyor. Tam takıma
  bağlandı.

**Belgelerdeki eski yollar düzeltildi.** Altı yerde motorun okumadığı
dosyalar tarif ediliyordu:

| Nerede | Eskiden | Doğrusu |
|--------|---------|---------|
| `proje-baslat.md` | `.claude/faz-plani.md`, `.claude/durum.md` | `hafiza/faz-plani.json`, `hafiza/durum.md` |
| `durum-kaydet.md` | `.claude/durum.md` + kırık depo yolu | `oturum.py bitir` |
| `faz-kontrol.md` | `.claude/faz-plani.md` okunuyordu | `faz.py durum` |
| `devir-ajani.md` | `.claude/durum.md` elle yazılıyordu | `oturum.py bitir` |
| `panel.md` | `.claude/durum.md` | `hafiza/durum.md` |

**Neden:** faz motoru planı `hafiza/faz-plani.json`, açılış brifingi durumu
`hafiza/durum.md` okuyor. Belgedeki yola yazılan dosya hiçbir yerde
görünmüyordu — komutu okuyup uygulayan kişi, işe yaramayan bir dosya
üretiyordu. Bu hata `/proje-devral` yazılırken fark edildi; orada
düzeltilmişti, kalan beş yer şimdi kapandı.

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
