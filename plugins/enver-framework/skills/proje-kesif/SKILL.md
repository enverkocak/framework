---
name: proje-kesif
description: Yeni bir proje, sistem, site, uygulama, panel ya da ozellik yapilacaksa - KODLAMAYA BASLAMADAN ONCE bu beceriyi kullan. Kullanici "yeni proje", "sunu yapalim", "bir sistem lazim", "su ozelligi ekleyelim" derse ya da bir isin nasil yapilacagini anlatmaya baslarsa, acikca istemese bile devreye gir. Amac: yarim anlasilmis bir ise baslayip sonra bastan yazmak zorunda kalmamak. Once istek toplanir, sonra arastirilir, sonra netlestirici sorular sorulur, ANCAK ONDAN SONRA kod yazilir.
---

# Proje keşfi

Enver'in kuralı (E19):

> Önce planlama modu olması gerekiyor projelerde ve araştırma modu.
> Önce neler olacağını, özellikleri soracak. Daha sonra da ekstra olabilecekleri
> araştıracak. Sonra sorular soracak, net öğrenip ona göre kodlamaya geçecek.

**Aşama atlanmaz.** En pahalı hata, yarım anlaşılmış bir işe başlayıp
sonra baştan yazmaktır.

## Dört aşama

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/plan/kesif.py"

python "$K" baslat --proje "<ad>" --musteri "<müşteri>"
python "$K" durum          # hangi aşamadayız
python "$K" sorular        # bu aşamada ne sorulacak
python "$K" yaz "<bulgu>"  # cevabı kaydet
python "$K" ilerle         # sonraki aşama
python "$K" ozet           # keşfin tamamı
python "$K" plana-dok      # faz planı üret
```

### 1. İSTEK TOPLAMA

Kullanıcıya sor, **varsayma**. Cevapları olduğu gibi kaydet.

- Bu iş ne yapacak? Tek cümleyle.
- Kim kullanacak, kaç kişi?
- Hangi sorunu çözüyor, şu an nasıl çözülüyor?
- Olmazsa olmazlar neler? Olsa iyi olurlar neler?
- Kesinlikle istenmeyen bir şey var mı?
- Ne zamana yetişmeli? Kapsam sınırı var mı?
- Mevcut sistem var mı, veri taşınacak mı?

Her cevabı `kesif.py yaz` ile kaydet. **Kullanıcının ağzından** yaz,
yorumlayarak değil.

### 2. ARAŞTIRMA

Şimdi kullanıcıya değil, işin kendisine bak. Amaç: **kullanıcının aklına
gelmeyen ama gerekli olacak** şeyleri bulmak.

- Benzer işlerde standart olarak ne bulunur?
- Bu işte en sık ne unutulur?
- Hangi teknik seçenekler var, artıları eksileri ne?
- Yasal zorunluluk var mı? (kişisel veri, fatura, arşiv süresi)
- Ölçek büyürse ne kırılır?
- Hangi dış servise bağımlı olacak, o kapanırsa ne olur?
- Yedek ve geri dönüş nasıl olacak?
- Bakımı kim yapacak?

Gerekirse gerçek araştırma yap: benzer sistemleri incele, örnek siteleri
çözümle (`/tasarim` altındaki `ilham.py site <adres>`), belge oku.

Bulguları kaydet. Bu aşamanın çıktısı **soru üretmek** içindir.

### 3. NETLEŞTİRME

Araştırmadan çıkan her maddeyi kullanıcıya sor. Belirsizlik bırakma.

- "Araştırmada şu çıktı — istiyor musunuz?"
- "Şu iki seçenekten hangisi, neden?"
- "Bu iş kimin sorumluluğunda: bizde mi, sizde mi?"
- "Kapsam dışı bıraktıklarımız kabul mü?"
- **"Hangi durumda 'bitti' diyeceğiz?"** — kabul ölçütü olmadan iş bitmez.

Birden çok soru varsa toplu sor, tek tek yorma.

### 4. PLAN

Fazlara böl. Her faza bir **kapı kontrolü** koy — "bitti" ölçülebilir olsun.

- Riskli parça erken denensin.
- İlk gösterilebilir sonuç erken çıksın.
- Her faz tek başına anlamlı olsun.

```bash
python "$K" plana-dok
```

Sonra faz motoruna aktar: `/faz` komutuna bak.

## Kodlamaya ne zaman geçilir

**Dördüncü aşama bitmeden geçilmez.** Kontrol:

```bash
python "$K" durum
```

"KODLAMAYA GEÇİLMEZ" yazıyorsa geçilmez. Kullanıcı ısrar ederse
eksik olanı söyle ve riski açıkça belirt.

## Küçük işler

Tek dosyalık bir düzeltme için dört aşama işletmek gereksizdir.
Ölçüt şu: **iş bir günden uzun sürecekse ya da müşteriye teslim edilecekse**
keşif yapılır.

Emin değilsen kullanıcıya sor: "Bunun için keşif yapalım mı, yoksa
doğrudan mı geçelim?"

## İlgili

- `/faz` — faz motoru ve kapı kontrolleri
- `/tasarim` — tasarım brifingi (keşiften sonra)
- `/projeler` — proje tanımı
